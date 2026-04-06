"""
Alert lifecycle helpers. Other subsystems (threshold evaluation, MQTT, etc.) should call
these functions rather than embedding SQL.

Extension hooks: after a successful insert, Twilio/SSE can subscribe to the same outcome
or listen for audit logs without changing the core insert path.

Simple explanation: The boss of alerts—create a new flag, mark it “someone noticed,”
mark it “all clear,” write a diary note (audit), ping live dashboards (SSE), and for
the worst level optionally send a text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.shared.alert import AlertCreate, AlertResponse
from app.shared.enums import AlertSeverity, AlertStatus
from app.shared.alert_sse_broadcaster import (
    ALERT_SSE_ACKNOWLEDGED,
    ALERT_SSE_CREATED,
    ALERT_SSE_RESOLVED,
    publish_alert_sse,
)
from app.shared.audit import log_audit_event

from . import alert_repository
from .notification_service import send_critical_alert_sms_if_configured


@dataclass(frozen=True)
class CreateAlertOutcome:
    """Result of attempting to create a new active alert."""

    created: bool
    alert: Optional[AlertResponse] = None
    skipped_duplicate_active: bool = False


@dataclass(frozen=True)
class AlertTransitionOutcome:
    """Result of acknowledge / resolve lifecycle operations."""

    alert: Optional[AlertResponse] = None
    not_found: bool = False
    invalid_transition: bool = False
    current_status: Optional[str] = None


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
        if inserted.severity == AlertSeverity.critical:
            send_critical_alert_sms_if_configured(inserted)
        publish_alert_sse(inserted, ALERT_SSE_CREATED)
        return CreateAlertOutcome(created=True, alert=inserted)

    @staticmethod
    def active_alert_exists_for_zone_metric(zone: str, metric: str) -> bool:
        """Convenience wrapper for callers that need to branch before heavier work."""
        return alert_repository.active_alert_exists_for_zone_metric(zone, metric)

    @staticmethod
    def list_alerts(
        *,
        status: Optional[AlertStatus] = None,
        zone: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> list[AlertResponse]:
        """Read-only list for operators; newest first in repository."""
        z = (zone or "").strip() or None
        return alert_repository.list_alerts(
            status=status, zone=z, severity=severity
        )

    @staticmethod
    def get_alert_by_id(alert_id: int) -> Optional[AlertResponse]:
        return alert_repository.get_alert_by_id(alert_id)

    @staticmethod
    def acknowledge_alert(alert_id: int) -> AlertTransitionOutcome:
        """active -> acknowledged (strict)."""
        updated = alert_repository.try_acknowledge_active_alert(alert_id)
        if updated is not None:
            log_audit_event(
                "alert.acknowledged",
                details={
                    "alert_id": updated.id,
                    "zone": updated.zone,
                    "metric": updated.metric,
                    "status": updated.status.value,
                },
            )
            publish_alert_sse(updated, ALERT_SSE_ACKNOWLEDGED)
            return AlertTransitionOutcome(alert=updated)

        previous = alert_repository.get_alert_by_id(alert_id)
        if previous is None:
            return AlertTransitionOutcome(not_found=True)
        return AlertTransitionOutcome(
            invalid_transition=True,
            current_status=previous.status.value,
        )

    @staticmethod
    def resolve_alert(alert_id: int) -> AlertTransitionOutcome:
        """active | acknowledged -> resolved."""
        updated = alert_repository.try_resolve_alert(alert_id)
        if updated is not None:
            log_audit_event(
                "alert.resolved",
                details={
                    "alert_id": updated.id,
                    "zone": updated.zone,
                    "metric": updated.metric,
                    "status": updated.status.value,
                },
            )
            publish_alert_sse(updated, ALERT_SSE_RESOLVED)
            return AlertTransitionOutcome(alert=updated)

        previous = alert_repository.get_alert_by_id(alert_id)
        if previous is None:
            return AlertTransitionOutcome(not_found=True)
        return AlertTransitionOutcome(
            invalid_transition=True,
            current_status=previous.status.value,
        )
