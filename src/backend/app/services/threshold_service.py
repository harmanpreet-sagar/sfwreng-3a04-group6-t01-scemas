"""
Threshold lifecycle business logic with audit logging.

This layer sits between the HTTP router and the database repository.
Keeping business rules here (rather than in the router or repository) means
they can be exercised without an HTTP request context — useful for background
tasks, CLI tools, and unit tests.

Responsibilities:
  - Orchestrate repository calls for each operation
  - Emit a structured audit event after every successful mutation
  - Return None for not-found cases so the router decides the HTTP status code

actor_email is passed in as a parameter (rather than extracted from a JWT
inside this service) to keep the service decoupled from HTTP/FastAPI concerns.
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
        """
        Persist a new threshold and emit a threshold.created audit event.

        The audit event is logged only after a successful DB write.  If the
        INSERT raises an exception nothing is logged, which correctly reflects
        that no threshold was actually created.
        """
        created = threshold_repository.insert_threshold(payload)
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
        """Return all thresholds (active and inactive). No audit needed for reads."""
        return threshold_repository.list_thresholds()

    @staticmethod
    def get_threshold(threshold_id: int) -> Optional[ThresholdResponse]:
        """
        Return one threshold by id, or None if it does not exist.

        The router converts None to a 404 response; this layer stays HTTP-free.
        No audit is emitted for read operations.
        """
        return threshold_repository.get_threshold_by_id(threshold_id)

    @staticmethod
    def update_threshold(
        threshold_id: int, changes: ThresholdUpdate, actor_email: str
    ) -> Optional[ThresholdResponse]:
        """
        Apply a partial update and emit a threshold.updated audit event.

        The audit details record only the changed fields (via exclude_none=True)
        so the audit trail shows a precise diff rather than the full row,
        making it easier to track what changed over time.
        Returns None without logging if the threshold does not exist.
        """
        updated = threshold_repository.update_threshold(threshold_id, changes)
        if updated is None:
            return None
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
        """
        Set is_active = TRUE and emit a threshold.activated audit event.

        Activating an already-active threshold is a no-op at the DB level but
        still emits an audit event so operators can see who triggered the call.
        Returns None if the threshold does not exist.
        """
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
        """
        Set is_active = FALSE and emit a threshold.deactivated audit event.

        Deactivated thresholds are hidden from the evaluator worker immediately
        on the next polling cycle but remain in the database for re-activation.
        Returns None if the threshold does not exist.
        """
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
        """
        Permanently remove a threshold and emit a threshold.deleted audit event.

        Audit is only logged when a row was actually deleted.  This prevents
        ghost audit entries if the router somehow calls delete twice on the same
        id (the second call would return False with no audit).
        """
        deleted = threshold_repository.delete_threshold(threshold_id)
        if deleted:
            log_audit_event(
                "threshold.deleted",
                details={"threshold_id": threshold_id, "actor": actor_email},
            )
        return deleted
