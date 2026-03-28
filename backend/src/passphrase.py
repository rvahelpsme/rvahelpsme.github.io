import os
import secrets
import hashlib
import binascii
import re

def _load_wordlist_internal():
    path = os.path.join(os.path.dirname(__file__), 'eff_wordlist.txt')
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

def generate_passphrase(num_words=3):
    return " ".join([secrets.choice(WORDLIST) for _ in range(num_words)])

def get_passphrase_hash(plain_phrase, pepper):
    if not pepper:
        raise ValueError("Pepper missing")
    return binascii.hexlify(hashlib.pbkdf2_hmac('sha256', plain_phrase.encode('utf-8'), pepper.encode('utf-8'), 600000)).decode('ascii')

def is_passphrase_in_use(supabase_client, plain_phrase, pepper):
    hashed = get_passphrase_hash(plain_phrase, pepper)
    result = supabase_client.table('passports').select('passphrase_hash').eq('passphrase_hash', hashed).execute()
    return len(result.data) > 0

def extract_passphrase(text):
    if not text:
        return None
    clean_text = re.sub(r'[^A-Za-z\s]', ' ', text)
    words = clean_text.upper().split()
    for i in range(len(words) - 2):
        triplet = words[i:i + 3]
        if all(word in WORDLIST_SET for word in triplet):
            return " ".join(triplet)
    return None