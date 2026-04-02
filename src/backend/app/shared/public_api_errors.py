"""
Structured error payloads for the public API (nested under FastAPI `detail`).

All values are JSON-serializable dicts; timestamps are UTC ISO-8601 with Z suffix.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def public_api_error_payload(
    *,
    error: str,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    """
    Standard public API error body. Use as HTTPException(..., detail=payload).

    Extra keyword arguments are merged in (None values are skipped).
    """
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    body: dict[str, Any] = {
        "error": error,
        "message": message,
        "timestamp": ts,
    }
    for key, value in extra.items():
        if value is not None:
            body[key] = value
    return body
