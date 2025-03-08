import json
import random
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/chat": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

OLLAMA_API_URL = "http://llm.informatik.uni-bremen.de:11434/api/chat"
EMOTIONS = [...]  # Your emotion list remains the same

# Preload GIF data at startup
with open('new_gif_urls.json') as f:
    gif_data = json.load(f)

EMOTION_PATTERN = re.compile(r"The emotion is \*\*(.*?)\*\*")
session = requests.Session()

@app.route('/chat', methods=['POST'])
@cross_origin(supports_credentials=True, allow_headers=['Content-Type'])
def chat():
    try:
        user_input = request.json.get("user_input")
        if not user_input:
            return jsonify({"error": "No input provided"}), 400

        system_prompt = (
            f"You are a friend who reacts naturally to stories and jokes. "
            f"First, state the likeliest emotion from: {', '.join(EMOTIONS)}. "
            f"Format as 'The emotion is **emotion**.' Then provide your response."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        # Use session and lower timeout
        response = session.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3",
                "messages": messages,
                "stream": False
            },
            timeout=10  # Adjust based on expected response time
        )

        if response.status_code != 200:
            return jsonify({"error": "API response error"}), 500

        data = response.json()
        full_response = data.get("message", {}).get("content", "").strip()

        # Use regex for parsing
        match = EMOTION_PATTERN.search(full_response)
        if match:
            emotion = match.group(1).lower()
            text = full_response[match.end():].strip()
        else:
            emotion = "relief"
            text = full_response

        # Get GIF URL from preloaded data
        selected_gif = random.choice(gif_data.get(emotion, ["default_gif_id"]))

        return jsonify({
            "text": text,
            "gif": selected_gif,
            "emotion": emotion
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Use in development only; production should use Gunicorn
    app.run(port=5050, debug=False)