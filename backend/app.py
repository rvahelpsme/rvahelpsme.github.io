import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime, timezone
from passphrase import generate_passphrase, get_passphrase_hash
from resources import get_verified_directory

load_dotenv()

app = Flask(__name__)
CORS(app)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("CRITICAL: SUPABASE_URL or SUPABASE_KEY missing from environment.")

supabase = create_client(supabase_url, supabase_key)

gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-3-flash-preview')


@app.route('/')
def index():
    return "Rhonda Backend V3 is live. Secure Passport routing active."


@app.route('/api/passport/create', methods=['POST'])
def create_passport():
    max_attempts = 5

    for attempt in range(max_attempts):
        plain_phrase = generate_passphrase()
        hashed_phrase = get_passphrase_hash(plain_phrase)

        response = supabase.table('passports').select('passphrase_hash').eq('passphrase_hash', hashed_phrase).execute()

        if not response.data:
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
    plain_phrase = data.get('passphrase').strip().upper()

    if not plain_phrase:
        return jsonify({"error": "Passphrase is required"}), 400

    hashed_phrase = get_passphrase_hash(plain_phrase)

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
    directory = get_verified_directory()

    if not directory:
        return jsonify({
            "response": "I'm having trouble accessing my verified resources right now. Please call 2-1-1 for immediate assistance with live interpreters.",
            "status": "fallback"
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)