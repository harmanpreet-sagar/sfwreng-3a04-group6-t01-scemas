"""Read-only alert endpoints for operations dashboards and history."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.alert import AlertListResponse, AlertResponse, AlertSeverity, AlertStatus
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


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
                "message": "No alert with this id",
                "alert_id": alert_id,
            },
        )
    return alert
