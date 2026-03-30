"""
SMS notifications via Twilio (proof-of-concept). Used for CRITICAL environmental alerts only.

Secrets come from environment variables only; never log tokens or message bodies with secrets.
"""

from __future__ import annotations

import logging
import os

from app.models.alert import AlertResponse

logger = logging.getLogger(__name__)

def _missing_twilio_env() -> list[str]:
    """SID, token, and recipient are required; sender is either FROM number or Messaging Service."""
    missing: list[str] = []
    for key in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_TO_NUMBER"):
        if not os.getenv(key, "").strip():
            missing.append(key)
    from_num = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    ms_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "").strip()
    if not from_num and not ms_sid:
        missing.append("TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID")
    return missing


def _format_critical_alert_sms(alert: AlertResponse) -> str:
    obs = (
        f"{alert.observed_value:g}"
        if alert.observed_value is not None
        else "n/a"
    )
    thr = (
        f"{alert.threshold_value:g}"
        if alert.threshold_value is not None
        else "n/a"
    )
    return (
        f"SCEMAS CRITICAL | zone={alert.zone} | metric={alert.metric} | "
        f"observed={obs} | threshold={thr} | alert_id={alert.id}"
    )


def send_critical_alert_sms_if_configured(alert: AlertResponse) -> None:
    """
    Send one SMS for a newly persisted CRITICAL alert.

    If Twilio is not fully configured, logs a warning and returns.
    If Twilio returns an error, logs and returns (alert is already in the DB).
    """
    missing = _missing_twilio_env()
    if missing:
        logger.warning(
            "Twilio SMS skipped for critical alert id=%s: set env %s",
            alert.id,
            ", ".join(missing),
        )
        return

    body = _format_critical_alert_sms(alert)

    try:
        from twilio.rest import Client

        client = Client(
            os.environ["TWILIO_ACCOUNT_SID"].strip(),
            os.environ["TWILIO_AUTH_TOKEN"].strip(),
        )
        to = os.environ["TWILIO_TO_NUMBER"].strip()
        ms_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "").strip()
        if ms_sid:
            client.messages.create(
                body=body,
                to=to,
                messaging_service_sid=ms_sid,
            )
        else:
            client.messages.create(
                body=body,
                to=to,
                from_=os.environ["TWILIO_FROM_NUMBER"].strip(),
            )
        logger.info("Twilio SMS sent for critical alert id=%s", alert.id)
    except Exception:
        logger.exception(
            "Twilio SMS failed for critical alert id=%s; alert record was still created",
            alert.id,
        )
