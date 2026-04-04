"""
Alerts endpoint tests — RBAC and happy paths (repository mocked).

Run from src/backend/:  pytest tests/test_alerts.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.shared.alert import AlertResponse
from app.shared.enums import AlertSeverity, AlertStatus

_NOW = datetime(2026, 4, 4, 12, 0, 0, tzinfo=timezone.utc)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _sample_alert(**overrides) -> AlertResponse:
    data = {
        "id": 1,
        "zone": "zone-1",
        "metric": "pm25",
        "severity": AlertSeverity.high,
        "message": "breach",
        "status": AlertStatus.active,
        "source_type": None,
        "observed_value": 99.0,
        "threshold_value": 50.0,
        "threshold_id": 1,
        "created_at": _NOW,
        "updated_at": _NOW,
        "acknowledged_at": None,
        "resolved_at": None,
    }
    data.update(overrides)
    return AlertResponse(**data)


class TestAlertsAuth:
    def test_list_no_token_returns_401(self, client):
        r = client.get("/alerts")
        assert r.status_code == 401
        assert r.json()["detail"]["error"] == "missing_token"

    def test_get_one_no_token_returns_401(self, client):
        r = client.get("/alerts/1")
        assert r.status_code == 401

    def test_ack_no_token_returns_401(self, client):
        r = client.patch("/alerts/1/acknowledge")
        assert r.status_code == 401

    def test_resolve_no_token_returns_401(self, client):
        r = client.patch("/alerts/1/resolve")
        assert r.status_code == 401

    def test_stream_no_token_returns_401(self, client):
        r = client.get("/alerts/stream")
        assert r.status_code == 401


class TestAlertsHappyPath:
    def test_list_with_operator_token(self, client, operator_token):
        with patch(
            "app.services.alert_repository.list_alerts",
            return_value=[],
        ):
            r = client.get("/alerts", headers=_auth(operator_token))
        assert r.status_code == 200
        assert r.json() == {"alerts": [], "total": 0}

    def test_list_with_admin_token(self, client, admin_token):
        row = _sample_alert()
        with patch(
            "app.services.alert_repository.list_alerts",
            return_value=[row],
        ):
            r = client.get("/alerts", headers=_auth(admin_token))
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["alerts"][0]["id"] == 1
        assert body["alerts"][0]["zone"] == "zone-1"

    def test_get_by_id_with_operator(self, client, operator_token):
        row = _sample_alert()
        with patch(
            "app.services.alert_repository.get_alert_by_id",
            return_value=row,
        ):
            r = client.get("/alerts/1", headers=_auth(operator_token))
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_stream_opens_with_auth(self, client, operator_token):
        from app.shared.alert_sse_broadcaster import alert_sse_broadcaster

        async def _fake_stream(_request):
            yield "data: {}\n\n"

        with patch.object(alert_sse_broadcaster, "stream", new=_fake_stream):
            r = client.get("/alerts/stream", headers=_auth(operator_token))
        assert r.status_code == 200
        assert "text/event-stream" in (r.headers.get("content-type") or "")
