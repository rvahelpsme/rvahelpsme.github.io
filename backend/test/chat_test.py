import os
import unittest
from google import genai
from dotenv import load_dotenv

from src.chat import build_system_instruction, get_rhonda_response
from src.resources import get_verified_directory

load_dotenv()


class TestChat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            cls.client = genai.Client(api_key=gemini_key)
        else:
            cls.client = None

        cls.live_directory = get_verified_directory()

        cls.initial_state = {
            "routing_preferences": {
                "needs_family_capacity": False,
                "needs_no_papers_intake": False
            },
            "active_intents": {
                "rental_assistance": "Seeking help paying current month rent."
            },
            "history": {
                "tried_resources": []
            },
            "language": "en"
        }

    def test_rhonda_updates_state_on_escalation(self):
        if not self.client:
            self.skipTest("GEMINI_API_KEY missing.")

        user_message = "That last place didn't have funding. Now I just received an eviction notice on my door."

        reply, new_state, status = get_rhonda_response(
            self.client,
            user_message,
            self.initial_state,
            self.live_directory
        )

        self.assertEqual(status, 200)
        self.assertIsInstance(reply, str)
        self.assertIsInstance(new_state, dict)

        state_str = str(new_state).lower()
        self.assertTrue("eviction" in state_str, f"State did not update to reflect eviction. State: {new_state}")

    def test_rhonda_returns_valid_fallback_on_json_error(self):
        class BadFormatClient:
            class chats:
                @staticmethod
                def create(**kwargs):
                    class FakeSession:
                        def send_message(self, msg):
                            class FakeResponse:
                                text = "This is just a normal text string, not JSON at all."

                            return FakeResponse()

                    return FakeSession()

        fake_client = BadFormatClient()
        reply, returned_state, status = get_rhonda_response(fake_client, "Hello", self.initial_state, [])

        self.assertEqual(status, 500)
        self.assertIn("System Error", reply)
        self.assertEqual(returned_state, self.initial_state)


if __name__ == "__main__":
    unittest.main()