import base64
import os
import re
import threading
from typing import Tuple, Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
from google import genai
from google.cloud import texttospeech

from src.static_responses import RESPONSES
from src.passphrase import (
    extract_passphrase, get_admin_state, get_resident_state,
    create_new_passport, save_resident_state_async, save_admin_updates_async
)
from src.resources import search_and_prune_directory
from src.chat import (
    execute_admin_prompt, execute_welcome_prompt,
    execute_classifier_prompt, execute_responder_prompt,
    execute_summary_prompt
)

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, 'gcp-key.json')

app = Flask(__name__)
CORS(app)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
pepper = os.environ.get("PASSPORT_PEPPER")

if not all([supabase_url, supabase_key, pepper]):
    raise ValueError("CRITICAL: Missing Supabase URL, Key, or Pepper from environment.")

supabase: Client = create_client(supabase_url, supabase_key)
gemini_key = os.environ.get("GEMINI_API_KEY")
ai_client = genai.Client(api_key=gemini_key) if gemini_key else None


def generate_tts_audio(text: str, lang_code: str = 'en'):
    try:
        client = texttospeech.TextToSpeechClient()
        voice_mapping = {
            "en": {"code": "en-US", "name": "en-US-Journey-F"},
            "es": {"code": "es-US", "name": "es-US-Neural2-A"},
            "pt": {"code": "pt-BR", "name": "pt-BR-Neural2-A"},
            "ar": {"code": "ar-XA", "name": "ar-XA-Wavenet-A"},
            "ne": {"code": "ne-NP", "name": "ne-NP-Wavenet-A"},
            "fa": {"code": "fa-IR", "name": "fa-IR-Wavenet-A"},
            "default": {"code": "en-US", "name": "en-US-Journey-F"}
        }
        selected = voice_mapping.get(lang_code, voice_mapping["default"])
        clean_text = text.replace('<br>', '\n').replace('<b>', '').replace('</b>', '')
        synthesis_input = texttospeech.SynthesisInput(text=clean_text)
        voice = texttospeech.VoiceSelectionParams(language_code=selected["code"], name=selected["name"])
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=0.95)
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return base64.b64encode(response.audio_content).decode('utf-8')
    except Exception as e:
        print(f"Google TTS Error: {e}")
        return None


def _format_suggested_resources(pruned_directory: list, ai_reply: str, state: dict) -> None:
    for resource in pruned_directory:
        org_name = resource.get('org_name') or ''
        service_name = resource.get('service_name') or ''
        dict_key = f"{service_name} (via {org_name})" if org_name else service_name
        if (org_name and org_name.lower() in ai_reply.lower()) or (
                service_name and service_name.lower() in ai_reply.lower()):
            if "resources_provided" not in state: state["resources_provided"] = {}
            raw_phone = resource.get('phone_number')
            state["resources_provided"][dict_key] = {"phone": raw_phone if raw_phone else "211", "status": "suggested"}


@app.route('/tts', methods=['POST'])
def get_audio():
    data = request.json
    text = data.get('text', '').strip()
    lang = data.get('lang', 'en')
    if not text: return jsonify({"error": "No text provided"}), 400
    audio_b64 = generate_tts_audio(text, lang)
    if audio_b64: return jsonify({"status": "success", "audio_base64": audio_b64}), 200
    return jsonify({"error": "Failed to generate audio"}), 500


@app.route('/summary', methods=['POST'])
def generate_summary():
    data = request.json
    session_hash = data.get('session_hash')
    target_lang = data.get('lang', 'en')
    if not session_hash: return jsonify({"error": "Session hash required"}), 400
    state, _ = get_resident_state(supabase, hash_only=session_hash)
    if not state: return jsonify({"error": "Passport not found"}), 404

    eng_summary, trans_summary, status = execute_summary_prompt(ai_client, state, target_lang)

    # NEW: Fetch the hardcoded explanation in the correct language
    explanation = RESPONSES["summary_explanation"].get(target_lang, RESPONSES["summary_explanation"]["en"])

    if status == 200:
        return jsonify({
            "status": "success",
            "english": eng_summary,
            "translated": trans_summary,
            "explanation": explanation
        }), 200

    return jsonify({"error": "Summary generation failed"}), 500


@app.route('/chat', methods=['POST'])
def chat():
    if not ai_client: return jsonify({"error": "AI client not configured."}), 500

    data = request.json
    user_message = data.get('message', '').strip()
    session_hash = data.get('session_hash')
    if not user_message: return jsonify({"error": "Message required"}), 400

    def get_ui_payload(lang):
        return {
            "greeting": RESPONSES["greeting"].get(lang, RESPONSES["greeting"]["en"]),
            "button_labels": RESPONSES["button_labels"].get(lang, RESPONSES["button_labels"]["en"])
        }

    signals = {
        "SIGNAL_INIT": "greeting",
        "SIGNAL_HOUSING": "housing_prompt",
        "SIGNAL_FOOD": "food_prompt",
        "SIGNAL_LEGAL": "legal_prompt",
        "SIGNAL_HEALTH": "healthcare_prompt",
        "SIGNAL_TRANSIT": "transportation_prompt",
        "SIGNAL_WORK": "workforce_prompt"
    }

    if user_message in signals:
        key = signals[user_message]
        lang_code = "en"
        is_new_user = False
        new_phrase = None
        active_hash = session_hash

        if session_hash:
            state, active_hash = get_resident_state(supabase, hash_only=session_hash)
            if state:
                lang_code = state.get("language", "en")
            else:
                state, active_hash, new_phrase = create_new_passport(supabase, pepper); is_new_user = True
        else:
            state, active_hash, new_phrase = create_new_passport(supabase, pepper)
            is_new_user = True

        reply = RESPONSES[key].get(lang_code, RESPONSES[key]["en"])
        payload = {
            "response": reply, "status": "success", "session_hash": active_hash, "language": lang_code,
            "is_static": True, "ui_translations": get_ui_payload(lang_code)
        }
        if is_new_user and new_phrase: payload["new_passphrase"] = new_phrase
        return jsonify(payload), 200

    clean_phrase, word_count = extract_passphrase(user_message)

    if word_count == 0:
        raw_words = re.sub(r'[^A-Za-z\s]', ' ', user_message).split()
        upper_sequence = sum(1 for w in raw_words if w.isupper() and len(w) > 1)
        if upper_sequence >= 3:
            return jsonify(
                {"response": "I couldn't find a record for that specific phrase.", "status": "not_found"}), 200

    if word_count == 4:
        admin_state, provider_hash = get_admin_state(supabase, clean_phrase, pepper)
        if not admin_state: return jsonify({"error": "Admin credentials not found."}), 404
        reply, db_updates, status_code = execute_admin_prompt(ai_client, user_message, admin_state)
        if db_updates: threading.Thread(target=save_admin_updates_async,
                                        args=(supabase, provider_hash, db_updates)).start()
        return jsonify({"response": reply, "status": "success", "session_hash": provider_hash}), status_code

    if word_count == 3:
        resident_state, passport_hash = get_resident_state(supabase, clean_phrase, pepper)
        if resident_state is None:
            failure_context = {"language": "en", "status": "passport_not_found"}
            reply, _ = execute_welcome_prompt(ai_client, f"SYSTEM_NOTIFY: Passport '{clean_phrase}' not found.",
                                              failure_context, clean_phrase)
            return jsonify({"response": reply, "status": "not_found"}), 200
        reply, status_code = execute_welcome_prompt(ai_client, user_message, resident_state, clean_phrase)
        return jsonify({
            "response": reply, "status": "success", "session_hash": passport_hash,
            "language": resident_state.get("language", "en"),
            "ui_translations": get_ui_payload(resident_state.get("language", "en"))
        }), status_code

    is_new_user = False
    new_phrase = None

    if session_hash:
        state, active_hash = get_resident_state(supabase, hash_only=session_hash)
        if not state:
            state, active_hash, new_phrase = create_new_passport(supabase, pepper)
            is_new_user = True
    else:
        state, active_hash, new_phrase = create_new_passport(supabase, pepper)
        is_new_user = True

    user_words = user_message.split()
    follow_up_triggers = {"number", "phone", "again", "what", "where", "name", "address"}
    is_follow_up = any(w in user_message.lower() for w in follow_up_triggers)

    if state.get("language") != "pending" and (len(user_words) < 7 or is_follow_up):
        is_vague = len(user_words) < 3 and not is_follow_up
        class_data = {
            "broad_buckets": [k for k, v in state.get("active_intents", {}).items() if v is True],
            "detected_language": state["language"], "needs_clarification": is_vague,
            "primary_urgency": state.get("active_intents", {}).get("primary"),
            "specific_intents": [], "user_demographics": [], "is_emergency": False, "static_intent": None
        }
        class_status = 200
    else:
        class_data, class_status = execute_classifier_prompt(ai_client, user_message)

    if class_status != 200: return jsonify({"error": "Classification failed."}), class_status

    if state.get("language") == "pending": state["language"] = class_data.get("detected_language", "en")
    locked_lang = state.get("language", "en")

    static_intent = class_data.get("static_intent")
    if static_intent and static_intent in RESPONSES:
        reply = RESPONSES[static_intent].get(locked_lang, RESPONSES[static_intent]["en"])
        payload = {
            "response": reply, "status": "success", "session_hash": active_hash, "language": locked_lang,
            "is_static": False, "ui_translations": get_ui_payload(locked_lang)
        }
        if is_new_user and new_phrase: payload["new_passphrase"] = new_phrase
        return jsonify(payload), 200

    state["active_intents"]["primary"] = class_data.get("primary_urgency")
    for bucket in class_data.get("broad_buckets", []): state["active_intents"][bucket] = True

    pruned_directory = []
    if class_data.get("needs_clarification"):
        state["_needs_clarification"] = True
    else:
        state["_needs_clarification"] = False
        pruned_directory = search_and_prune_directory(supabase, class_data, locked_lang)

    reply, updated_state, resp_status = execute_responder_prompt(ai_client, user_message, state, pruned_directory)
    updated_state.pop("_needs_clarification", None)

    if pruned_directory: _format_suggested_resources(pruned_directory, reply, updated_state)

    if resp_status != 200: return jsonify({"error": "Response generation failed."}), resp_status

    threading.Thread(target=save_resident_state_async, args=(supabase, active_hash, updated_state)).start()

    response_payload = {
        "response": reply, "status": "success", "session_hash": active_hash,
        "language": updated_state.get("language", "en"), "is_static": False,
        "ui_translations": get_ui_payload(updated_state.get("language", "en"))
    }
    if is_new_user and new_phrase: response_payload["new_passphrase"] = new_phrase

    return jsonify(response_payload)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)