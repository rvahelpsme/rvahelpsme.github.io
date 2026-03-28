import unittest
from app import app
from src.passphrase import WORDLIST


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.test_passphrase = None

    def test_1_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Rhonda Backend", response.data)

    def test_2_create_passport(self):
        response = self.client.post('/api/passport/create')
        self.assertEqual(response.status_code, 201)

        data = response.get_json()
        self.assertIn("passphrase", data)
        self.assertIn("state_json", data)

        TestApp.test_passphrase = data["passphrase"]

    def test_3_access_passport_valid(self):
        if not TestApp.test_passphrase:
            self.skipTest("Passport creation failed, skipping access test.")

        response = self.client.post('/api/passport/access', json={
            "passphrase": TestApp.test_passphrase
        })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("state_json", data)

    def test_4_access_passport_invalid_format(self):
        response = self.client.post('/api/passport/access', json={
            "passphrase": "NOT A REAL PHRASE AT ALL"
        })
        self.assertEqual(response.status_code, 400)

    def test_5_access_passport_not_found(self):
        valid_format_fake_phrase = f"{WORDLIST[0]} {WORDLIST[1]} {WORDLIST[2]}"

        response = self.client.post('/api/passport/access', json={
            "passphrase": valid_format_fake_phrase
        })
        self.assertEqual(response.status_code, 404)

    def test_6_access_passport_missing_data(self):
        response = self.client.post('/api/passport/access', json={})
        self.assertEqual(response.status_code, 400)

    def test_7_chat_valid_passport(self):
        if not TestApp.test_passphrase:
            self.skipTest("Passport creation failed, skipping chat test.")

        response = self.client.post('/chat', json={
            "passphrase": TestApp.test_passphrase,
            "message": "Hello, I am testing the system. I need housing assistance."
        })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("response", data)

    def test_8_chat_invalid_format(self):
        response = self.client.post('/chat', json={
            "passphrase": "TOTALLY FAKE FAKE FAKE",
            "message": "Hello"
        })
        self.assertEqual(response.status_code, 400)

    def test_9_chat_passport_not_found(self):
        valid_format_fake_phrase = f"{WORDLIST[0]} {WORDLIST[1]} {WORDLIST[2]}"

        response = self.client.post('/chat', json={
            "passphrase": valid_format_fake_phrase,
            "message": "Hello"
        })
        self.assertEqual(response.status_code, 404)

    def test_10_chat_missing_data(self):
        response = self.client.post('/chat', json={
            "passphrase": TestApp.test_passphrase
        })
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()