"""
Threshold Management endpoints.

These routes let operators and admins query thresholds, and admins create,
modify, activate, deactivate, or delete them.  Every mutating operation is
forwarded through ThresholdService so the audit log is always populated.

RBAC summary:
  GET  /threshold              — OPERATOR + ADMIN  (read-only ops open to both)
  GET  /threshold/{id}         — OPERATOR + ADMIN
  POST /threshold              — ADMIN only
  PATCH /threshold/{id}        — ADMIN only
  PATCH /threshold/{id}/activate   — ADMIN only
  PATCH /threshold/{id}/deactivate — ADMIN only
  DELETE /threshold/{id}       — ADMIN only

Route ordering note: /activate and /deactivate must be declared before
/{threshold_id} so FastAPI's router matches literal path segments first.
If the wildcard route were declared first, a request to
PATCH /threshold/activate would be consumed by it with threshold_id="activate",
resulting in a confusing 422 type-validation error instead of a clean match.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.shared.auth import CurrentUser, require_admin, require_operator_or_admin
from app.shared.threshold import ThresholdCreate, ThresholdResponse, ThresholdUpdate
from app.services.threshold_service import ThresholdService

router = APIRouter(prefix="/threshold", tags=["Threshold Management"])

_NOT_FOUND_DETAIL = "No threshold with this id"


def _not_found(threshold_id: int) -> HTTPException:
    """
    Build a structured 404 HTTPException for a missing threshold.

    Centralising this keeps every 404 in the router identical in shape,
    which makes it easy for API consumers to pattern-match on the `error`
    key without brittle message-string comparisons.
    """
    return HTTPException(
        status_code=404,
        detail={
            "error": "threshold_not_found",
            "message": _NOT_FOUND_DETAIL,
            "threshold_id": threshold_id,
        },
    )


@router.post("", response_model=ThresholdResponse, status_code=201)
def create_threshold(
    payload: ThresholdCreate,
    current_user: CurrentUser = Depends(require_admin),
) -> ThresholdResponse:
    """
    Create a new threshold rule.

    The request body is validated by Pydantic (ThresholdCreate) before this
    handler is called, so no manual field checks are needed here.
    Responds 201 with the newly created row including its auto-assigned id.
    """
    return ThresholdService.create_threshold(payload, actor_email=current_user.email)


@router.get("", response_model=list[ThresholdResponse])
def list_thresholds(
    _: CurrentUser = Depends(require_operator_or_admin),
) -> list[ThresholdResponse]:
    """
    Return all thresholds ordered by id.

    The `_` parameter name signals that the resolved CurrentUser is not used
    inside this handler — we only need the Depends to enforce authentication.
    Both active and inactive thresholds are returned so operators can see the
    full configured set, not just the ones the evaluator is currently checking.
    """
    return ThresholdService.list_thresholds()


@router.get("/{threshold_id}", response_model=ThresholdResponse)
def get_threshold(
    threshold_id: int,
    _: CurrentUser = Depends(require_operator_or_admin),
) -> ThresholdResponse:
    """
    Return a single threshold by id.

    Returns 404 with a structured error body if the id does not exist in the
    database, rather than letting a None propagate and produce a 500.
    """
    threshold = ThresholdService.get_threshold(threshold_id)
    if threshold is None:
        raise _not_found(threshold_id)
    return threshold


@router.patch("/{threshold_id}", response_model=ThresholdResponse)
def update_threshold(
    threshold_id: int,
    changes: ThresholdUpdate,
    current_user: CurrentUser = Depends(require_admin),
) -> ThresholdResponse:
    """
    Partially update a threshold's fields.

    ThresholdUpdate uses Optional fields so callers only send the properties
    they want to change.  Sending an empty body {} is legal and returns the
    unchanged row with 200 (the repository skips the DB write in that case).
    """
    updated = ThresholdService.update_threshold(
        threshold_id, changes, actor_email=current_user.email
    )
    if updated is None:
        raise _not_found(threshold_id)
    return updated


@router.patch("/{threshold_id}/activate", response_model=ThresholdResponse)
def activate_threshold(
    threshold_id: int,
    current_user: CurrentUser = Depends(require_admin),
) -> ThresholdResponse:
    """
    Set is_active = TRUE for a threshold, making it visible to the evaluator.

    Activating an already-active threshold is a no-op but still returns 200
    with the current row so the caller can confirm the final state.
    """
    updated = ThresholdService.activate_threshold(
        threshold_id, actor_email=current_user.email
    )
    if updated is None:
        raise _not_found(threshold_id)
    return updated


@router.patch("/{threshold_id}/deactivate", response_model=ThresholdResponse)
def deactivate_threshold(
    threshold_id: int,
    current_user: CurrentUser = Depends(require_admin),
) -> ThresholdResponse:
    """
    Set is_active = FALSE for a threshold, hiding it from the evaluator.

    Useful when an operator wants to temporarily pause a rule without deleting
    it — the configuration is preserved and can be re-activated later.
    """
    updated = ThresholdService.deactivate_threshold(
        threshold_id, actor_email=current_user.email
    )
    if updated is None:
        raise _not_found(threshold_id)
    return updated


# response_class=Response is required when status_code=204: FastAPI 0.115+
# validates that a 204 response has no body, which conflicts with its default
# JSONResponse wrapper.  Returning Response(status_code=204) explicitly
# satisfies that contract while still triggering the 404 branch above.
@router.delete("/{threshold_id}", status_code=204, response_class=Response)
def delete_threshold(
    threshold_id: int,
    current_user: CurrentUser = Depends(require_admin),
) -> Response:
    """
    Permanently delete a threshold by id.

    Returns 204 No Content on success.  Consider deactivate instead when you
    want a recoverable "soft delete" — this operation is irreversible and will
    also remove the row from the evaluator's active set immediately.
    """
    deleted = ThresholdService.delete_threshold(
        threshold_id, actor_email=current_user.email
    )
    if not deleted:
        raise _not_found(threshold_id)
    return Response(status_code=204)
