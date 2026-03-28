import os
import json
import re


def build_system_instruction(state, context_data, is_admin=False):
    base_dir = os.path.dirname(os.path.dirname(__file__))

    if is_admin:
        prompt_path = os.path.join(base_dir, 'ADMIN_PROMPT.txt')
        context_label = "PROVIDER_RESOURCES (CURRENT DB STATE)"
    else:
        prompt_path = os.path.join(base_dir, 'MASTER_PROMPT.txt')
        context_label = "VERIFIED_DIRECTORY (TRUTH)"

    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read().strip()
    except FileNotFoundError:
        return f"CRITICAL ERROR: Could not find {os.path.basename(prompt_path)}"

    instruction = (
        f"{base_prompt}\n\n"
        f"STATE (JSON):\n{json.dumps(state)}\n\n"
        f"{context_label}:\n{json.dumps(context_data)}"
    )

    return instruction


def get_rhonda_response(client, user_message, state, context_data, is_admin=False):
    system_instruction = build_system_instruction(state, context_data, is_admin)

    if "CRITICAL ERROR" in system_instruction:
        return "System configuration error: Missing prompt files.", state, 500

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
        db_updates = parsed_response.get("database_updates", [])  # Extract the updates

        return reply, updated_state, db_updates, 200  # Return 4 items now

    except json.JSONDecodeError:
        return "System Error: The AI returned improperly formatted data.", state, [], 500
    except Exception as e:
        return f"AI Generation Error: {str(e)}", state, [], 500