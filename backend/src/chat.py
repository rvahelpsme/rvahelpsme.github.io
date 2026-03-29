import json
from typing import Tuple, Dict, Any
from google.genai import types
from src.promptbuilder import build_prompt

def _call_gemini(ai_client, prompt_text: str, schema: dict) -> dict:
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash', contents=prompt_text,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema, temperature=0.1)
    )
    return json.loads(response.text)

def _merge_state_safely(current_state: dict, new_state: dict) -> None:
    protected_keys = ["intake_prep", "active_intents", "routing_preferences", "resources_provided"]
    for key in protected_keys:
        if key in new_state and isinstance(new_state[key], dict):
            if key not in current_state: current_state[key] = {}
            current_state[key].update(new_state[key])
    if new_state.get("language") and new_state["language"] != "pending":
        current_state["language"] = new_state["language"]

def execute_classifier_prompt(ai_client, user_message: str) -> Tuple[Dict[str, Any], int]:
    prompt_text = build_prompt('classifier', user_message)
    schema = {
        "type": "OBJECT",
        "properties": {
            "broad_buckets": {"type": "ARRAY", "items": {"type": "STRING"}},
            "specific_intents": {"type": "ARRAY", "items": {"type": "STRING"}},
            "user_demographics": {"type": "ARRAY", "items": {"type": "STRING"}},
            "primary_urgency": {"type": "STRING", "nullable": True},
            "detected_language": {"type": "STRING"},
            "is_emergency": {"type": "BOOLEAN"},
            "needs_clarification": {"type": "BOOLEAN"},
            "static_intent": {"type": "STRING", "nullable": True}
        }
    }
    try: return _call_gemini(ai_client, prompt_text, schema), 200
    except Exception as e: print(f"Classifier Error: {e}"); return {}, 500

def execute_responder_prompt(ai_client, user_message: str, state: dict, pruned_directory: list) -> Tuple[str, dict, int]:
    prompt_text = build_prompt('responder', user_message, state=state, context_data=pruned_directory)
    schema = {
        "type": "OBJECT",
        "properties": {
            "reply": {"type": "STRING"},
            "updated_state": {
                "type": "OBJECT",
                "properties": {
                    "language": {"type": "STRING"}, "intake_prep": {"type": "OBJECT"},
                    "active_intents": {"type": "OBJECT"}, "routing_preferences": {"type": "OBJECT"},
                    "resources_provided": {"type": "OBJECT"}
                },
                "required": ["language", "intake_prep", "active_intents", "routing_preferences", "resources_provided"]
            }
        },
        "required": ["reply", "updated_state"]
    }
    try:
        data = _call_gemini(ai_client, prompt_text, schema)
        reply_text = data.get("reply", "I am having trouble connecting. Please dial 211 for immediate Virginia crisis support.")
        _merge_state_safely(state, data.get("updated_state", {}))
        return reply_text, state, 200
    except Exception as e:
        print(f"Responder Error: {e}"); return "System error. Please dial VA 211 for assistance.", state, 500

def execute_welcome_prompt(ai_client, user_message: str, state: dict, passphrase: str) -> Tuple[str, int]:
    prompt_text = build_prompt('welcome', user_message, state=state, passphrase=passphrase)
    schema = {"type": "OBJECT", "properties": {"reply": {"type": "STRING"}}}
    try: return _call_gemini(ai_client, prompt_text, schema).get("reply", "Welcome back."), 200
    except: return "Welcome back.", 500

def execute_admin_prompt(ai_client, user_message: str, admin_state: dict) -> Tuple[str, dict, int]:
    prompt_text = build_prompt('admin', user_message, state=admin_state)
    schema = {"type": "OBJECT", "properties": {"reply": {"type": "STRING"}, "db_updates": {"type": "OBJECT"}}}
    try:
        data = _call_gemini(ai_client, prompt_text, schema)
        return data.get("reply", "Understood."), data.get("db_updates", {}), 200
    except: return "Admin portal error.", {}, 500

def execute_summary_prompt(ai_client, state: dict, target_lang: str) -> Tuple[str, str, int]:
    prompt_text = build_prompt('summary', "", state=state)
    schema = {"type": "OBJECT", "properties": {"english_summary": {"type": "STRING"}, "translated_summary": {"type": "STRING"}}}
    try:
        data = _call_gemini(ai_client, prompt_text, schema)
        return data.get("english_summary", "Summary unavailable."), data.get("translated_summary", "Summary unavailable."), 200
    except: return "System Error", "System Error", 500