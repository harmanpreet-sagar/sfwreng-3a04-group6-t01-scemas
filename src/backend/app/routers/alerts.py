"""Alert endpoints: read list/detail and lifecycle (acknowledge / resolve)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.models.alert import AlertListResponse, AlertResponse, AlertSeverity, AlertStatus
from app.services.alert_service import AlertService
from app.shared.alert_sse_broadcaster import alert_sse_broadcaster

router = APIRouter(prefix="/alerts", tags=["Alerts"])

_NOT_FOUND_DETAIL = "No alert with this id"


@router.get("", response_model=AlertListResponse)
def get_alerts(
    status: Optional[AlertStatus] = Query(
        None, description="Filter by lifecycle status"
    ),
    zone: Optional[str] = Query(
        None, description="Exact match on zone", min_length=1
    ),
    severity: Optional[AlertSeverity] = Query(
        None, description="Filter by severity"
    ),
) -> AlertListResponse:
    rows = AlertService.list_alerts(status=status, zone=zone, severity=severity)
    return AlertListResponse(alerts=rows, total=len(rows))


@router.get("/stream")
async def alert_event_stream(request: Request) -> StreamingResponse:
    """Server-Sent Events stream of new/updated alerts (in-memory PoC)."""
    return StreamingResponse(
        alert_sse_broadcaster.stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int) -> AlertResponse:
    outcome = AlertService.acknowledge_alert(alert_id)
    if outcome.alert is not None:
        return outcome.alert
    if outcome.not_found:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "alert_not_found",
                "message": _NOT_FOUND_DETAIL,
                "alert_id": alert_id,
            },
        )
    raise HTTPException(
        status_code=409,
        detail={
            "error": "invalid_state_transition",
            "message": "Only alerts with status 'active' can be acknowledged.",
            "alert_id": alert_id,
            "current_status": outcome.current_status,
            "allowed_from": ["active"],
        },
    )


@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int) -> AlertResponse:
    outcome = AlertService.resolve_alert(alert_id)
    if outcome.alert is not None:
        return outcome.alert
    if outcome.not_found:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "alert_not_found",
                "message": _NOT_FOUND_DETAIL,
                "alert_id": alert_id,
            },
        )
    raise HTTPException(
        status_code=409,
        detail={
            "error": "invalid_state_transition",
            "message": (
                "Only alerts with status 'active' or 'acknowledged' can be resolved."
            ),
            "alert_id": alert_id,
            "current_status": outcome.current_status,
            "allowed_from": ["active", "acknowledged"],
        },
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    responses={
        404: {
            "description": "Alert not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": "alert_not_found",
                            "message": "No alert with this id",
                            "alert_id": 0,
                        }
                    }
                }
            },
        }
    },
)
def get_alert(alert_id: int) -> AlertResponse:
    alert = AlertService.get_alert_by_id(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "alert_not_found",
                "message": _NOT_FOUND_DETAIL,
                "alert_id": alert_id,
            },
        )
    return alert
