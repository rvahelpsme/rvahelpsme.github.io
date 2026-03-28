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
    return "Rhonda Backend V3 is live. Secure Passport routing active."


@app.route('/api/passport/create', methods=['POST'])
def create_passport():
    max_attempts = 5

    for _ in range(max_attempts):
        plain_phrase = generate_passphrase()

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

    clean_phrase = extract_passphrase(raw_phrase)
    if not clean_phrase:
        return jsonify({"error": "Valid passphrase is required"}), 400

    hashed_phrase = get_passphrase_hash(clean_phrase, pepper)
    response = supabase.table('passports').select('*').eq('passphrase_hash', hashed_phrase).execute()

    if not response.data:
        return jsonify({"error": "Passport not found or invalid passphrase."}), 404

    passport_data = response.data[0]

    try:
        supabase.table('passports').update({
            "last_accessed_at": datetime.now(timezone.utc).isoformat()
        }).eq('passphrase_hash', hashed_phrase).execute()
    except Exception as e:
        print(f"Warning: Non-fatal error updating access timestamp: {e}")

    return jsonify({
        "status": "success",
        "state_json": passport_data['state_json']
    }), 200


@app.route('/chat', methods=['POST'])
def chat():
    if not ai_client:
        return jsonify({"error": "AI client not configured."}), 500

    data = request.json
    user_message = data.get('message', '').strip()
    raw_phrase = data.get('passphrase', '')

    clean_phrase = extract_passphrase(raw_phrase)
    if not user_message or not clean_phrase:
        return jsonify({"error": "Message and valid Passphrase required"}), 400

    hashed_phrase = get_passphrase_hash(clean_phrase, pepper)
    passport_res = supabase.table('passports').select('state_json').eq('passphrase_hash', hashed_phrase).execute()

    if not passport_res.data:
        return jsonify({"error": "Passport not found."}), 404

    state = passport_res.data[0]['state_json']

    directory = get_verified_directory()
    if not directory:
        return jsonify({
            "response": "I'm having trouble connecting to my resource list. Please call 2-1-1 for immediate assistance.",
            "status": "fallback"
        })

    reply, new_state, status_code = get_rhonda_response(ai_client, user_message, state, directory)

    if status_code != 200:
        return jsonify({"error": reply}), status_code

    try:
        supabase.table('passports').update({
            "state_json": new_state,
            "last_accessed_at": datetime.now(timezone.utc).isoformat()
        }).eq('passphrase_hash', hashed_phrase).execute()
    except Exception as e:
        pass

    return jsonify({
        "response": reply,
        "status": "success"
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)