import os
import secrets
import hashlib
import binascii

WORDLIST_PATH = os.path.join(os.path.dirname(__file__), 'eff_wordlist.txt')


def load_wordlist(filepath=WORDLIST_PATH):
    words = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    words.append(parts[1])
        if not words:
            raise ValueError(f"CRITICAL: Wordlist at {filepath} is empty or improperly formatted.")
        return words
    except FileNotFoundError:
        raise FileNotFoundError(f"CRITICAL: Wordlist missing at {filepath}. Cannot generate passphrases.")


def generate_passphrase(num_words=3):
    words = load_wordlist()
    passphrase = [secrets.choice(words).upper() for _ in range(num_words)]
    return " ".join(passphrase)


def get_passphrase_hash(passphrase):
    pepper = os.environ.get("PASSPORT_PEPPER")
    if not pepper:
        raise ValueError(
            "CRITICAL: PASSPORT_PEPPER environment variable is missing. Halting to prevent insecure hashing.")

    hash_bytes = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=passphrase.encode('utf-8'),
        salt=pepper.encode('utf-8'),
        iterations=600000
    )

    return binascii.hexlify(hash_bytes).decode('ascii')