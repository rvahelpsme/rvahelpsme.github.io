import os
import secrets
import hashlib
import binascii
import re

def _load_wordlist_internal():
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

def generate_passphrase(num_words=3):
    return " ".join([secrets.choice(WORDLIST) for _ in range(num_words)])

def get_passphrase_hash(plain_phrase, pepper):
    if not pepper:
        raise ValueError("Pepper missing")
    return binascii.hexlify(hashlib.pbkdf2_hmac('sha256', plain_phrase.encode('utf-8'), pepper.encode('utf-8'), 600000)).decode('ascii')

def is_passphrase_in_use(supabase_client, plain_phrase, pepper):
    words = plain_phrase.split()
    count = len(words)
    hashed = get_passphrase_hash(plain_phrase, pepper)

    if count == 4:
        res = supabase_client.table('providers').select('passphrase_hash').eq('passphrase_hash', hashed).execute()
        if len(res.data) > 0:
            return True

        prefix_phrase = " ".join(words[:3])
        suffix_phrase = " ".join(words[1:])

        return is_passphrase_in_use(supabase_client, prefix_phrase, pepper) or \
            is_passphrase_in_use(supabase_client, suffix_phrase, pepper)

    if count == 3:
        res = supabase_client.table('passports').select('passphrase_hash').eq('passphrase_hash', hashed).execute()
        return len(res.data) > 0

    raise ValueError(f"Invalid passphrase length: {count}")

def extract_passphrase(text):
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