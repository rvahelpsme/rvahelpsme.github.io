import os
import secrets
import hashlib
import binascii
import re
import datetime
from typing import Tuple, Optional

def _load_wordlist_internal() -> list:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, 'eff_wordlist.txt')
    words = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    words.append(parts[1].upper())
        if not words:
            raise ValueError(f"Wordlist empty at {path}")
        return words
    except FileNotFoundError:
        raise ValueError(f"Wordlist not at {path}")

WORDLIST = _load_wordlist_internal()
WORDLIST_SET = set(WORDLIST)

def generate_passphrase(num_words: int = 3) -> str:
    return " ".join([secrets.choice(WORDLIST) for _ in range(num_words)])

def get_passphrase_hash(plain_phrase: str, pepper: str) -> str:
    if not pepper:
        raise ValueError("Pepper missing")
    return binascii.hexlify(
        hashlib.pbkdf2_hmac('sha256', plain_phrase.encode('utf-8'), pepper.encode('utf-8'), 100000)
    ).decode('ascii')

def is_passphrase_in_use(supabase_client, plain_phrase: str, pepper: str) -> bool:
    words = plain_phrase.split()
    count = len(words)
    hashed = get_passphrase_hash(plain_phrase, pepper)

    if count == 4:
        res = supabase_client.table('providers').select('passphrase_hash').eq('passphrase_hash', hashed).execute()
        if len(res.data) > 0:
            return True
        prefix_phrase = " ".join(words[:3])
        suffix_phrase = " ".join(words[1:])
        return is_passphrase_in_use(supabase_client, prefix_phrase, pepper) or is_passphrase_in_use(supabase_client, suffix_phrase, pepper)

    if count == 3:
        res = supabase_client.table('passports').select('passphrase_hash').eq('passphrase_hash', hashed).execute()
        return len(res.data) > 0

    raise ValueError(f"Invalid passphrase length: {count}")

def extract_passphrase(text: str) -> Tuple[Optional[str], int]:
    if not text:
        return None, 0

    clean_text = re.sub(r'[^A-Za-z\s]', ' ', text)
    words = clean_text.upper().split()

    first_triplet = None
    run_start = 0
    run_len = 0

    for i, word in enumerate(words):
        if word in WORDLIST_SET:
            if run_len == 0:
                run_start = i
            run_len += 1
            if run_len == 4:
                return " ".join(words[run_start:run_start + 4]), 4
        else:
            if run_len == 3 and first_triplet is None:
                first_triplet = " ".join(words[run_start:run_start + 3])
            run_len = 0

    if run_len == 3 and first_triplet is None:
        first_triplet = " ".join(words[run_start:run_start + 3])

    return (first_triplet, 3) if first_triplet else (None, 0)

def create_new_passport(supabase_client, pepper: str) -> Tuple[dict, str, str]:
    while True:
        new_phrase = generate_passphrase(3)
        if not is_passphrase_in_use(supabase_client, new_phrase, pepper):
            break

    new_hash = get_passphrase_hash(new_phrase, pepper)
    default_state = {
        "language": "pending",
        "intake_prep": {},
        "active_intents": {},
        "routing_preferences": {"needs_family_capacity": False, "needs_no_papers_intake": False},
        "resources_provided": {}
    }

    supabase_client.table('passports').insert({
        "passphrase_hash": new_hash,
        "state_json": default_state
    }).execute()

    return default_state, new_hash, new_phrase

def get_resident_state(supabase_client, phrase: str = None, pepper: str = None, hash_only: str = None) -> Tuple[Optional[dict], Optional[str]]:
    target_hash = hash_only if hash_only else get_passphrase_hash(phrase, pepper)
    response = supabase_client.table('passports').select('state_json').eq('passphrase_hash', target_hash).execute()
    if response.data:
        return response.data[0]['state_json'], target_hash
    return None, None

def get_admin_state(supabase_client, phrase: str, pepper: str) -> Tuple[Optional[dict], Optional[str]]:
    target_hash = get_passphrase_hash(phrase, pepper)
    response = supabase_client.table('providers').select('*').eq('passphrase_hash', target_hash).execute()
    if response.data:
        return {"role": "admin"}, target_hash
    return None, None

def save_resident_state_async(supabase_client, target_hash: str, state: dict) -> None:
    try:
        supabase_client.table('passports').update({
            "state_json": state,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }).eq('passphrase_hash', target_hash).execute()
    except Exception as e:
        print(f"Error saving resident state: {e}")

def save_admin_updates_async(supabase_client, provider_hash: str, updates: dict) -> None:
    if not updates or not isinstance(updates, dict):
        return
    try:
        supabase_client.table('resources').update(updates).eq('provider_hash', provider_hash).execute()
    except Exception as e:
        print(f"Error saving admin updates: {e}")