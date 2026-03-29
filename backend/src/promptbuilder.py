import os
import json
from typing import Optional


def _read_prompt_file(filename: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    path = os.path.join(root_dir, 'prompts', filename)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"[CRITICAL ERROR: Missing {filename}]"


def build_prompt(prompt_type: str, user_message: str, state: Optional[dict] = None, context_data: Optional[list] = None,
                 passphrase: Optional[str] = None) -> str:
    master_prompt = _read_prompt_file('MASTER_PROMPT.txt')
    language_rules = _read_prompt_file('LANGUAGE_RULES.txt')

    msg_text = f"User: {user_message}"
    if prompt_type not in ['welcome', 'summary'] and any(w in user_message.lower() for w in ["passport", "passphrase"]):
        msg_text += "\n\n[SYSTEM ALERT: The user mentioned a passport or passphrase, but the system did NOT recognize the words. Gently inform them the phrase was invalid and ask how else you can assist.]"

    stack = [master_prompt, "\n--- USER MESSAGE ---", msg_text]

    if prompt_type == 'classifier':
        stack.extend(["\n--- ACTION: INTENT CLASSIFIER ---", _read_prompt_file('ACTION_CLASSIFIER.txt')])

    elif prompt_type == 'responder':
        stack.extend([
            "\n--- LANGUAGE RULES ---", language_rules,
            "\n--- CONTEXT DATA (PRUNED DIRECTORY) ---", json.dumps(context_data or [], indent=2),
            "\n--- ACTION: RESPOND TO USER ---", _read_prompt_file('ACTION_RESPONDER.txt'),
            "\n--- CURRENT STATE ---", json.dumps(state or {}, indent=2)
        ])

    elif prompt_type == 'welcome':
        user_lang = state.get('language', 'pending') if state else 'pending'
        greeting_lang = 'en' if user_lang == 'pending' else user_lang
        bypass_note = f"[System Note: The user authenticated with phrase '{passphrase}'. Ignore the English words of the phrase. Welcome them exclusively in '{greeting_lang}'.]"

        stack.extend([
            "\n--- LANGUAGE RULES ---", language_rules,
            "\n--- ACTION: WELCOME BACK ---", bypass_note, _read_prompt_file('ACTION_WELCOME.txt'),
            "\n--- CURRENT STATE ---", json.dumps(state or {}, indent=2)
        ])

    elif prompt_type == 'admin':
        stack.extend([
            "\n--- CONTEXT DATA (PROVIDER RESOURCES) ---", json.dumps(context_data or [], indent=2),
            "\n--- ACTION: PROVIDER PORTAL ---", _read_prompt_file('ACTION_ADMIN.txt'),
            "\n--- CURRENT STATE ---", json.dumps(state or {}, indent=2)
        ])

    elif prompt_type == 'summary':
        target_lang = state.get('language', 'en') if state else 'en'
        stack.extend([
            "\n--- ACTION: GENERATE PROVIDER SUMMARY ---",
            f"Review the CURRENT STATE object. Write a short, professional bulleted summary of the user's needs to hand to a social worker. Output it once in English, and once translated into the language code: '{target_lang}'.",
            "\n--- CURRENT STATE ---", json.dumps(state or {}, indent=2)
        ])

    else:
        return f"System Error: Unknown prompt_type '{prompt_type}'"

    return "\n\n".join(stack)