import os
import json
import re


def build_system_instruction(state, directory):
    prompt_path = os.path.join(os.path.dirname(__file__), 'master_prompt.txt')

    with open(prompt_path, 'r', encoding='utf-8') as f:
        base_prompt = f.read().strip()

    return f"{base_prompt}\n\nUSER_PROFILE (ANONYMOUS):\n{json.dumps(state)}\n\nVERIFIED_DIRECTORY (TRUTH):\n{json.dumps(directory)}"


def get_rhonda_response(client, user_message, state, directory):
    system_instruction = build_system_instruction(state, directory)

    try:
        chat_session = client.chats.create(
            model='gemini-3-flash-preview',
            config={'system_instruction': system_instruction}
        )
        response = chat_session.send_message(user_message)

        raw_text = response.text.strip()
        clean_text = re.sub(r'^```json\s*', '', raw_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\s*```$', '', clean_text)

        parsed_response = json.loads(clean_text)

        reply = parsed_response.get("reply", "I encountered an error generating my response.")
        updated_state = parsed_response.get("updated_state", state)

        return reply, updated_state, 200

    except json.JSONDecodeError:
        return "System Error: The AI returned improperly formatted data.", state, 500
    except Exception as e:
        return f"AI Generation Error: {str(e)}", state, 500