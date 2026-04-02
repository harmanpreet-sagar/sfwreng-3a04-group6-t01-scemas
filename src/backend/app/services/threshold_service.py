"""
Threshold lifecycle helpers with audit logging.

Responsibilities of this layer:
  - Orchestrate repository calls
  - Emit audit events for every mutation
  - Return None for not-found cases so the router decides the HTTP status

actor_email is passed in as a parameter (rather than fetched from the JWT
inside this layer) to keep the service decoupled from HTTP concerns — it can
be called from background tasks or tests without a live request context.
"""

from __future__ import annotations

from typing import Optional

from app.shared.audit import log_audit_event
from app.shared.threshold import ThresholdCreate, ThresholdResponse, ThresholdUpdate
from app.services import threshold_repository


class ThresholdService:
    @staticmethod
    def create_threshold(
        payload: ThresholdCreate, actor_email: str
    ) -> ThresholdResponse:
        created = threshold_repository.insert_threshold(payload)
        # Audit is logged after a successful DB write — if the insert fails,
        # no audit record is emitted, which correctly reflects nothing happened.
        log_audit_event(
            "threshold.created",
            details={
                "threshold_id": created.id,
                "zone": created.zone,
                "metric": created.metric,
                "condition": created.condition.value,
                "threshold_value": created.threshold_value,
                "severity": created.severity.value,
                "actor": actor_email,
            },
        )
        return created

    @staticmethod
    def list_thresholds() -> list[ThresholdResponse]:
        return threshold_repository.list_thresholds()

    @staticmethod
    def get_threshold(threshold_id: int) -> Optional[ThresholdResponse]:
        return threshold_repository.get_threshold_by_id(threshold_id)

    @staticmethod
    def update_threshold(
        threshold_id: int, changes: ThresholdUpdate, actor_email: str
    ) -> Optional[ThresholdResponse]:
        updated = threshold_repository.update_threshold(threshold_id, changes)
        if updated is None:
            return None
        # Log the diff rather than the full row so the audit trail shows
        # exactly which fields were changed without storing redundant data.
        log_audit_event(
            "threshold.updated",
            details={
                "threshold_id": threshold_id,
                "changes": changes.model_dump(exclude_none=True),
                "actor": actor_email,
            },
        )
        return updated

    @staticmethod
    def activate_threshold(
        threshold_id: int, actor_email: str
    ) -> Optional[ThresholdResponse]:
        updated = threshold_repository.set_threshold_active(threshold_id, is_active=True)
        if updated is None:
            return None
        log_audit_event(
            "threshold.activated",
            details={"threshold_id": threshold_id, "actor": actor_email},
        )
        return updated

    @staticmethod
    def deactivate_threshold(
        threshold_id: int, actor_email: str
    ) -> Optional[ThresholdResponse]:
        updated = threshold_repository.set_threshold_active(threshold_id, is_active=False)
        if updated is None:
            return None
        log_audit_event(
            "threshold.deactivated",
            details={"threshold_id": threshold_id, "actor": actor_email},
        )
        return updated

    @staticmethod
    def delete_threshold(threshold_id: int, actor_email: str) -> bool:
        deleted = threshold_repository.delete_threshold(threshold_id)
        # Only audit if the row actually existed — prevents ghost audit entries
        # if the router somehow calls delete twice on the same id.
        if deleted:
            log_audit_event(
                "threshold.deleted",
                details={"threshold_id": threshold_id, "actor": actor_email},
            )
        return deleted
