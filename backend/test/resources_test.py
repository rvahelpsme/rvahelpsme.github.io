import sys
import os
import unittest
from dotenv import load_dotenv

from src.resources import get_verified_directory

load_dotenv()


class TestResources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory_data = get_verified_directory()

    def test_directory_fetch_returns_data(self):
        if not self.directory_data:
            self.skipTest("Live sheet unavailable or returned empty.")
        self.assertGreater(len(self.directory_data), 0)

    def test_directory_data_preserves_dynamic_headers(self):
        if not self.directory_data:
            self.skipTest("Live sheet unavailable or returned empty.")

        first_row = self.directory_data[0]
        self.assertIsInstance(first_row, dict)
        self.assertGreater(len(first_row.keys()), 0)

        for key in first_row.keys():
            self.assertIsInstance(key, str)
            self.assertTrue(len(key) > 0)

    def test_directory_data_drops_empty_rows(self):
        if not self.directory_data:
            self.skipTest("Live sheet unavailable or returned empty.")

        for row in self.directory_data:
            has_data = any(val is not None and str(val).strip() != '' for val in row.values())
            self.assertTrue(has_data)


if __name__ == "__main__":
    unittest.main()