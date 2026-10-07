"""Unit tests for SecretRedactor."""

import unittest
from brain.security.redactor import SecretRedactor

class TestSecretRedactor(unittest.TestCase):
    def test_redacts_gemini_key(self):
        text = "Using API key AIzaSyD3x9Z1234567890abcdefABCDEFGHI12 for gemini"
        redacted = SecretRedactor.redact_text(text)
        self.assertNotIn("AIzaSyD3x", redacted)
        self.assertIn("[REDACTED_GEMINI_KEY]", redacted)

    def test_redacts_github_token(self):
        text = "Export token ghp_1234567890abcdefghijklmnopqrstuvwxyzAB"
        redacted = SecretRedactor.redact_text(text)
        self.assertNotIn("ghp_12345", redacted)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", redacted)

    def test_redacts_env_secret(self):
        text = "DATABASE_PASSWORD='super_secret_db_password_123' host=localhost"
        redacted = SecretRedactor.redact_text(text)
        self.assertNotIn("super_secret_db_password_123", redacted)
        self.assertIn("[REDACTED_ENV_SECRET]", redacted)

    def test_redacts_nested_json(self):
        data = {
            "config": {
                "auth": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.do_not_leak_this_token",
                "normal": "hello world"
            }
        }
        res = SecretRedactor.redact_json_obj(data)
        self.assertEqual(res["config"]["normal"], "hello world")
        self.assertTrue(
            "[REDACTED_BEARER_TOKEN]" in res["config"]["auth"] or "[REDACTED_JWT]" in res["config"]["auth"]
        )

if __name__ == "__main__":
    unittest.main()
