import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables for local testing
load_dotenv()

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return "Rhonda Backend is live."


@app.route('/')
def health():
    return jsonify({"status": "healthy"}), 200


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    # Placeholder for Gemini and Database logic
    return jsonify({
        "response": f"Rhonda received your message: {user_message}",
        "status": "success"
    })


if __name__ == '__main__':
    # Render provides the PORT environment variable automatically
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)