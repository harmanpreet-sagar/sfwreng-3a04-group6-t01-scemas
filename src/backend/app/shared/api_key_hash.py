"""SHA-256 hex digest for API key material (must match seeding in api_key_seed)."""

from __future__ import annotations

import hashlib


def api_key_sha256_hex(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
