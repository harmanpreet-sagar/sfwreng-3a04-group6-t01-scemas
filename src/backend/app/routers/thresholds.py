"""
Threshold Management endpoints.

RBAC:
  GET  /threshold          — OPERATOR + ADMIN
  GET  /threshold/{id}     — OPERATOR + ADMIN
  POST /threshold          — ADMIN only
  PATCH /threshold/{id}    — ADMIN only
  PATCH /threshold/{id}/activate   — ADMIN only
  PATCH /threshold/{id}/deactivate — ADMIN only
  DELETE /threshold/{id}   — ADMIN only

Route ordering note: /activate and /deactivate are declared before
/{threshold_id} so FastAPI matches the literal path segments first.
If the wildcard route were declared first, GET /threshold/activate
would be consumed by it and treated as threshold_id="activate".
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
    # Extracted so every 404 in this router has the same shape, making it
    # easier for callers to pattern-match on `error` without checking message text.
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
    return ThresholdService.create_threshold(payload, actor_email=current_user.email)


@router.get("", response_model=list[ThresholdResponse])
def list_thresholds(
    _: CurrentUser = Depends(require_operator_or_admin),
) -> list[ThresholdResponse]:
    return ThresholdService.list_thresholds()


@router.get("/{threshold_id}", response_model=ThresholdResponse)
def get_threshold(
    threshold_id: int,
    _: CurrentUser = Depends(require_operator_or_admin),
) -> ThresholdResponse:
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
    deleted = ThresholdService.delete_threshold(
        threshold_id, actor_email=current_user.email
    )
    if not deleted:
        raise _not_found(threshold_id)
    return Response(status_code=204)
