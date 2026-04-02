#!/usr/bin/env python3
"""
Send one test SMS via Twilio using the same env vars as notification_service.

Run from src/backend (with venv active):

  PYTHONPATH=. python scripts/test_twilio_sms.py

Loads .env from src/.env and src/backend/.env (same order as main.py).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parent.parent
_src_env = _backend_dir.parent / ".env"
load_dotenv(_src_env)
load_dotenv(_backend_dir / ".env")


def main() -> int:
    # Reuse the same completeness check as production SMS.
    from app.services.notification_service import _missing_twilio_env

    missing = _missing_twilio_env()
    if missing:
        print("Missing or incomplete Twilio configuration:", ", ".join(missing), file=sys.stderr)
        return 1

    body = "SCEMAS Twilio test — you can delete this message."
    try:
        from twilio.rest import Client

        client = Client(
            os.environ["TWILIO_ACCOUNT_SID"].strip(),
            os.environ["TWILIO_AUTH_TOKEN"].strip(),
        )
        to = os.environ["TWILIO_TO_NUMBER"].strip()
        ms_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "").strip()
        if ms_sid:
            msg = client.messages.create(
                body=body,
                to=to,
                messaging_service_sid=ms_sid,
            )
        else:
            msg = client.messages.create(
                body=body,
                to=to,
                from_=os.environ["TWILIO_FROM_NUMBER"].strip(),
            )
        print("Sent. Twilio Message SID:", msg.sid)
        return 0
    except Exception as e:
        print("Twilio API error:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
