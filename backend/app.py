import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
from google import genai
from datetime import datetime, timezone

from src.passphrase import generate_passphrase, get_passphrase_hash, is_passphrase_in_use, extract_passphrase
from src.resources import get_verified_directory
from src.chat import get_rhonda_response

load_dotenv()

app = Flask(__name__)
# Restrict CORS in production if possible, but keeping open for the hackathon sprint
CORS(app)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
pepper = os.environ.get("PASSPORT_PEPPER")

if not all([supabase_url, supabase_key, pepper]):
    raise ValueError("CRITICAL: Missing Supabase URL, Key, or Pepper from environment.")

supabase = create_client(supabase_url, supabase_key)

gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    ai_client = genai.Client(api_key=gemini_key)
else:
    ai_client = None


@app.route('/')
def index():
    return "Rhonda Backend V4 is live. 3-Word Resident and 4-Word Admin routing active."


@app.route('/api/passport/create', methods=['POST'])
def create_passport():
    max_attempts = 5

    for _ in range(max_attempts):
        plain_phrase = generate_passphrase(num_words=3)  # Explicitly 3 words for residents

        if not is_passphrase_in_use(supabase, plain_phrase, pepper):
            hashed_phrase = get_passphrase_hash(plain_phrase, pepper)

            default_state = {
                "routing_preferences": {
                    "needs_family_capacity": False,
                    "needs_no_papers_intake": False
                },
                "active_intents": {},
                "language": "en",
                "intake_prep": {}
            }

            try:
                supabase.table('passports').insert({
                    "passphrase_hash": hashed_phrase,
                    "state_json": default_state
                }).execute()

                return jsonify({
                    "status": "success",
                    "passphrase": plain_phrase,
                    "state_json": default_state
                }), 201
            except Exception as e:
                return jsonify({"error": f"Database insertion failed: {str(e)}"}), 500

    return jsonify({"error": "Failed to generate a unique passport after multiple attempts."}), 500


@app.route('/api/passport/access', methods=['POST'])
def access_passport():
    data = request.json
    raw_phrase = data.get('passphrase', '')

    # FIX: Unpack the tuple correctly
    clean_phrase, word_count = extract_passphrase(raw_phrase)

    if not clean_phrase:
        return jsonify({"error": "Valid passphrase is required"}), 400

    hashed_phrase = get_passphrase_hash(clean_phrase, pepper)

    # Check which table to query based on word count
    table_name = 'providers' if word_count == 4 else 'passports'
    response = supabase.table(table_name).select('*').eq('passphrase_hash', hashed_phrase).execute()

    if not response.data:
        return jsonify({"error": "Credential not found or invalid passphrase."}), 404

    record_data = response.data[0]

    try:
        supabase.table(table_name).update({
            "last_accessed": datetime.now(timezone.utc).isoformat()
        }).eq('passphrase_hash', hashed_phrase).execute()
    except Exception as e:
        print(f"Warning: Non-fatal error updating access timestamp: {e}")

    # Return the appropriate payload
    if word_count == 4:
        return jsonify({
            "status": "success",
            "role": "admin",
            "provider_hash": hashed_phrase
        }), 200
    else:
        return jsonify({
            "status": "success",
            "role": "resident",
            "state_json": record_data['state_json']
        }), 200


@app.route('/chat', methods=['POST'])
def chat():
    if not ai_client:
        return jsonify({"error": "AI client not configured."}), 500

    data = request.json
    user_message = data.get('message', '').strip()
    current_hash = data.get('session_hash')  # Hidden frontend state

    if not user_message:
        return jsonify({"error": "Message required"}), 400

    # 1. Scan the message for a new passphrase
    clean_phrase, word_count = extract_passphrase(user_message)

    is_admin = False
    active_hash = current_hash
    state = {}
    new_phrase_generated = None

    # 2. If the user typed a phrase in chat, it overrides their current session
    if clean_phrase:
        active_hash = get_passphrase_hash(clean_phrase, pepper)
        if word_count == 4:
            is_admin = True
            provider_res = supabase.table('providers').select('*').eq('passphrase_hash', active_hash).execute()
            if not provider_res.data:
                return jsonify({"error": "Admin credentials not found."}), 404
            resources_res = supabase.table('resources').select('*').eq('provider_hash', active_hash).execute()
            state = {"managed_resources": resources_res.data}
        elif word_count == 3:
            passport_res = supabase.table('passports').select('state_json').eq('passphrase_hash', active_hash).execute()
            if not passport_res.data:
                return jsonify({"error": "Passport not found."}), 404
            state = passport_res.data[0]['state_json']

    # 3. If no phrase in chat, check for an existing session hash
    elif current_hash:
        # Check if it's a provider session first
        provider_res = supabase.table('providers').select('*').eq('passphrase_hash', current_hash).execute()
        if provider_res.data:
            is_admin = True
            resources_res = supabase.table('resources').select('*').eq('provider_hash', current_hash).execute()
            state = {"managed_resources": resources_res.data}
        else:
            passport_res = supabase.table('passports').select('state_json').eq('passphrase_hash',
                                                                               current_hash).execute()
            if not passport_res.data:
                # Session is invalid or deleted, clear it out
                active_hash = None
            else:
                state = passport_res.data[0]['state_json']

    # 4. If completely anonymous (no phrase in chat, no active session), create one
    if not active_hash and not is_admin:
        new_phrase_generated = generate_passphrase(num_words=3)
        active_hash = get_passphrase_hash(new_phrase_generated, pepper)
        state = {
            "routing_preferences": {"needs_family_capacity": False, "needs_no_papers_intake": False},
            "active_intents": {},
            "language": "en",
            "intake_prep": {}
        }
        supabase.table('passports').insert({
            "passphrase_hash": active_hash,
            "state_json": state
        }).execute()

    # 5. Fetch directory and talk to Rhonda
    directory = [] if is_admin else get_verified_directory()

    # --- AI CONTEXT INTERCEPT ---
    # Tell Rhonda what those random words mean so she doesn't get confused
    llm_message = user_message
    if clean_phrase:
        llm_message = (
            f"[System Note: The user just successfully authenticated using the secure phrase '{clean_phrase}'. "
            f"Their saved state is loaded. If their message below is ONLY the phrase, warmly welcome them back. "
            f"Otherwise, answer their question normally.]\n\nUser: {user_message}"
        )
    # ----------------------------

    reply, new_state, status_code = get_rhonda_response(
        ai_client,
        llm_message,  # Pass the intercepted message, not the raw user_message
        state,
        directory,
        is_admin=is_admin
    )

    if status_code != 200:
        return jsonify({"error": reply}), status_code

    # 6. Save state if it's a resident
    if not is_admin:
        try:
            supabase.table('passports').update({
                "state_json": new_state,
                "last_accessed": datetime.now(timezone.utc).isoformat()
            }).eq('passphrase_hash', active_hash).execute()
        except Exception:
            pass

    response_payload = {
        "response": reply,
        "status": "success",
        "session_hash": active_hash
    }

    if new_phrase_generated:
        response_payload["new_passphrase"] = new_phrase_generated

    return jsonify(response_payload)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)