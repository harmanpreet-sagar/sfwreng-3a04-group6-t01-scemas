"""
Alert lifecycle helpers. Other subsystems (threshold evaluation, MQTT, etc.) should call
these functions rather than embedding SQL.

Extension hooks: after a successful insert, Twilio/SSE can subscribe to the same outcome
or listen for audit logs without changing the core insert path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.alert import AlertCreate, AlertResponse
from app.shared.audit import log_audit_event

from . import alert_repository


@dataclass(frozen=True)
class CreateAlertOutcome:
    """Result of attempting to create a new active alert."""

    created: bool
    alert: Optional[AlertResponse] = None
    skipped_duplicate_active: bool = False


class AlertService:
    @staticmethod
    def create_alert(payload: AlertCreate) -> CreateAlertOutcome:
        """
        Persist a new active alert when no active alert exists for the same zone + metric.

        New rows always use status `active` regardless of any other status on `payload`
        (reserved for future copy/clone flows).
        """
        inserted = alert_repository.try_insert_active_alert(payload)
        if inserted is None:
            return CreateAlertOutcome(
                created=False,
                skipped_duplicate_active=True,
            )

        log_audit_event(
            "alert.created",
            details={
                "alert_id": inserted.id,
                "zone": inserted.zone,
                "metric": inserted.metric,
                "severity": inserted.severity.value,
                "threshold_id": inserted.threshold_id,
            },
        )
        return CreateAlertOutcome(created=True, alert=inserted)

    @staticmethod
    def active_alert_exists_for_zone_metric(zone: str, metric: str) -> bool:
        """Convenience wrapper for callers that need to branch before heavier work."""
        return alert_repository.active_alert_exists_for_zone_metric(zone, metric)
