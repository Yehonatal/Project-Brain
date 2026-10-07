"""High-assurance secret and PII redaction engine.

Protects against storing or leaking API keys, private keys, tokens,
and high-entropy secrets in SQLite or over the MCP server.
"""

import math
import re
from typing import Any, Dict, List, Tuple

# Pre-compiled high-confidence secret patterns
SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # Google API / Gemini keys
    ("GEMINI_KEY", re.compile(r"AIza[0-9A-Za-z\-_]{30,}")),
    # OpenAI keys
    ("OPENAI_KEY", re.compile(r"sk-[a-zA-Z0-9]{20,T3BlbkFJ[a-zA-Z0-9]{20,}|sk-proj-[a-zA-Z0-9_\-]{40,}")),
    # GitHub Personal Access Tokens
    ("GITHUB_TOKEN", re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}")),
    # AWS Access Keys
    ("AWS_KEY", re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}")),
    # Slack Tokens
    ("SLACK_TOKEN", re.compile(r"xox[baprs]-[0-9A-Za-z\-]{20,}")),
    # Generic Bearer Tokens
    ("BEARER_TOKEN", re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}")),
    # PEM Private Keys
    ("PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    # .env key-value secrets (PASSWORD=..., DATABASE_PASSWORD=..., SECRET=...)
    (
        "ENV_SECRET",
        re.compile(
            r"(?i)\b[a-zA-Z0-9_]*(?:password|passwd|secret|api_key|apikey|access_token|auth_token|client_secret)\s*[:=]\s*['\"]?([^\s'\"&;]{6,})['\"]?"
        ),
    ),
    # JSON web tokens (JWT)
    ("JWT", re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")),
]

def shannon_entropy(data: str) -> float:
    """Calculates the Shannon entropy of a string."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for x in set(data):
        p_x = float(data.count(x)) / length
        entropy += -p_x * math.log(p_x, 2)
    return entropy

class SecretRedactor:
    """Detects and redacts sensitive credentials, tokens, and high-entropy strings."""

    @classmethod
    def redact_text(cls, text: str) -> str:
        if not text:
            return ""

        redacted = text

        # 1. Apply known regex patterns
        for label, pattern in SECRET_PATTERNS:
            if label == "ENV_SECRET":
                # For env patterns, only redact the captured secret value, keep the variable name
                def replace_env(m):
                    full = m.group(0)
                    val = m.group(1)
                    return full.replace(val, f"[REDACTED_{label}]")
                redacted = pattern.sub(replace_env, redacted)
            else:
                redacted = pattern.sub(f"[REDACTED_{label}]", redacted)

        # 2. Entropy check on suspicious standalone alphanumeric tokens
        # Check tokens longer than 24 chars that look like random base64 or hex
        words = redacted.split()
        for word in words:
            clean_word = word.strip("\"'()[]{},;:")
            if len(clean_word) >= 28 and re.match(r"^[A-Za-z0-9+/=_-]+$", clean_word):
                if not clean_word.startswith("[REDACTED"):
                    entropy = shannon_entropy(clean_word)
                    if entropy > 4.2:  # High randomness threshold typical for API keys/hashes
                        redacted = redacted.replace(clean_word, "[REDACTED_HIGH_ENTROPY]")

        return redacted

    @classmethod
    def redact_json_obj(cls, obj: Any) -> Any:
        """Recursively redacts dictionary and list structures."""
        if isinstance(obj, str):
            return cls.redact_text(obj)
        elif isinstance(obj, dict):
            return {k: cls.redact_json_obj(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls.redact_json_obj(item) for item in obj]
        return obj
