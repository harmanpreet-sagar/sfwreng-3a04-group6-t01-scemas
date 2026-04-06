"""
Structured audit logging for operational traceability.

Uses the stdlib logging stack so deployments can route `scemas.audit` to JSON sinks
or log aggregators without a separate audit table (PoC-friendly).

Simple explanation (alerts): When the alert boss creates an alert, it writes a dated
“what happened” line here so grown-ups can trace it later.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Mapping

_audit_logger = logging.getLogger("scemas.audit")


def log_audit_event(event_type: str, details: Mapping[str, Any] | None = None) -> None:
    """Emit one audit record as a single JSON log line."""
    payload: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
    }
    if details:
        payload["details"] = dict(details)
    _audit_logger.info("%s", json.dumps(payload, default=str))
