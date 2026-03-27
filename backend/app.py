import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Setup Clients
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3-flash-preview')
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))


@app.route('/')
def index():
    return "Rhonda Backend V3 is live."

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    try:
        system_instruction = "You are Rhonda, a helpful assistant for people in housing crises in Richmond, VA."
        full_prompt = f"{system_instruction}\n\nUser asks: {user_message}"

        response = model.generate_content(full_prompt)

        return jsonify({
            "response": response.text,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "response": f"Error connecting to AI: {str(e)}",
            "status": "error"
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)