import os
import unittest
from dotenv import load_dotenv
from supabase import create_client

from src.passphrase import WORDLIST, generate_passphrase, get_passphrase_hash, is_passphrase_in_use, extract_passphrase

load_dotenv()
PEPPER = os.environ.get("PASSPORT_PEPPER")
SUPABASE = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

class TestPassphrase(unittest.TestCase):
    def test_generate_format(self):
        phrase = generate_passphrase()
        self.assertEqual(len(phrase.split()), 3)
        self.assertTrue(phrase.isupper())

    def test_hash_consistency(self):
        phrase = "TEST PHRASE CODE"
        self.assertEqual(get_passphrase_hash(phrase, PEPPER), get_passphrase_hash(phrase, PEPPER))

    def test_hash_no_pepper(self):
        with self.assertRaises(ValueError):
            get_passphrase_hash("TEST", None)

    def test_extract_messy(self):
        w1, w2, w3 = WORDLIST[0], WORDLIST[1], WORDLIST[2]
        self.assertEqual(extract_passphrase(f"Code: ({w1.lower()}-{w2.lower()}-{w3.lower()})!"), f"{w1} {w2} {w3}")

    def test_extract_none(self):
        self.assertIsNone(extract_passphrase("NOT A CODE"))

    def test_is_in_use_false(self):
        self.assertFalse(is_passphrase_in_use(SUPABASE, f"UNIQUE {os.urandom(4).hex()}", PEPPER))

if __name__ == "__main__":
    unittest.main()