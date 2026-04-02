"""
Threshold Management endpoint tests.

All repository calls are mocked — no real DB required.
Run from src/backend/:  pytest tests/test_thresholds.py -v

Patching strategy: we patch at the repository layer (not the service layer)
so each test exercises the full router → service → repository call chain.
Only the actual SQL execution is bypassed, which means RBAC decisions, audit
event emission, and None-handling in the service are all covered by the suite.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.shared.enums import AlertSeverity, ThresholdCondition
from app.shared.threshold import ThresholdResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)


def _make_threshold(id: int = 1, **overrides) -> ThresholdResponse:
    """Return a ThresholdResponse with sensible defaults.

    **overrides lets individual tests swap out only the fields they care about
    without repeating the full payload every time.
    """
    data = {
        "id": id,
        "zone": "zone-1",
        "metric": "pm25",
        "condition": ThresholdCondition.gt,
        "threshold_value": 50.0,
        "severity": AlertSeverity.high,
        "is_active": True,
        "created_at": _NOW,
        "updated_at": _NOW,
    }
    data.update(overrides)
    return ThresholdResponse(**data)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Auth / RBAC tests  (no DB calls needed)
# ---------------------------------------------------------------------------

class TestAuth:
    def test_get_list_no_token_returns_401(self, client):
        r = client.get("/threshold")
        assert r.status_code == 401
        assert r.json()["detail"]["error"] == "missing_token"

    def test_post_no_token_returns_401(self, client):
        r = client.post("/threshold", json={})
        assert r.status_code == 401

    def test_post_as_operator_returns_403(self, client, operator_token):
        with patch("app.services.threshold_repository.insert_threshold"):
            r = client.post(
                "/threshold",
                json={
                    "zone": "z",
                    "metric": "m",
                    "condition": "gt",
                    "threshold_value": 1.0,
                    "severity": "low",
                },
                headers=_auth(operator_token),
            )
        assert r.status_code == 403
        assert r.json()["detail"]["error"] == "forbidden"

    def test_delete_as_operator_returns_403(self, client, operator_token):
        r = client.delete("/threshold/1", headers=_auth(operator_token))
        assert r.status_code == 403

    def test_patch_as_operator_returns_403(self, client, operator_token):
        r = client.patch(
            "/threshold/1",
            json={"threshold_value": 99.0},
            headers=_auth(operator_token),
        )
        assert r.status_code == 403

    def test_activate_as_operator_returns_403(self, client, operator_token):
        r = client.patch("/threshold/1/activate", headers=_auth(operator_token))
        assert r.status_code == 403

    def test_deactivate_as_operator_returns_403(self, client, operator_token):
        r = client.patch("/threshold/1/deactivate", headers=_auth(operator_token))
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /threshold
# ---------------------------------------------------------------------------

class TestListThresholds:
    def test_admin_gets_empty_list(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.list_thresholds", return_value=[]
        ):
            r = client.get("/threshold", headers=_auth(admin_token))
        assert r.status_code == 200
        assert r.json() == []

    def test_operator_can_list(self, client, operator_token):
        with patch(
            "app.services.threshold_repository.list_thresholds",
            return_value=[_make_threshold(1), _make_threshold(2)],
        ):
            r = client.get("/threshold", headers=_auth(operator_token))
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_list_returns_correct_fields(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.list_thresholds",
            return_value=[_make_threshold()],
        ):
            r = client.get("/threshold", headers=_auth(admin_token))
        item = r.json()[0]
        assert item["zone"] == "zone-1"
        assert item["metric"] == "pm25"
        assert item["condition"] == "gt"
        assert item["threshold_value"] == 50.0
        assert item["severity"] == "high"
        assert item["is_active"] is True


# ---------------------------------------------------------------------------
# GET /threshold/{id}
# ---------------------------------------------------------------------------

class TestGetThreshold:
    def test_get_existing_threshold(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.get_threshold_by_id",
            return_value=_make_threshold(7),
        ):
            r = client.get("/threshold/7", headers=_auth(admin_token))
        assert r.status_code == 200
        assert r.json()["id"] == 7

    def test_get_nonexistent_returns_404(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.get_threshold_by_id",
            return_value=None,
        ):
            r = client.get("/threshold/999", headers=_auth(admin_token))
        assert r.status_code == 404
        assert r.json()["detail"]["error"] == "threshold_not_found"

    def test_operator_can_get_by_id(self, client, operator_token):
        with patch(
            "app.services.threshold_repository.get_threshold_by_id",
            return_value=_make_threshold(3),
        ):
            r = client.get("/threshold/3", headers=_auth(operator_token))
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST /threshold
# ---------------------------------------------------------------------------

class TestCreateThreshold:
    _payload = {
        "zone": "zone-1",
        "metric": "pm25",
        "condition": "gt",
        "threshold_value": 50.0,
        "severity": "high",
        "is_active": True,
    }

    def test_admin_creates_threshold(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.insert_threshold",
            return_value=_make_threshold(1),
        ):
            r = client.post(
                "/threshold",
                json=self._payload,
                headers=_auth(admin_token),
            )
        assert r.status_code == 201
        body = r.json()
        assert body["id"] == 1
        assert body["zone"] == "zone-1"
        assert body["metric"] == "pm25"

    def test_create_invalid_condition_returns_422(self, client, admin_token):
        # Pydantic rejects unknown enum values before the handler is called,
        # so no repository patch is needed here.
        bad = {**self._payload, "condition": "INVALID"}
        r = client.post("/threshold", json=bad, headers=_auth(admin_token))
        assert r.status_code == 422

    def test_create_missing_field_returns_422(self, client, admin_token):
        incomplete = {k: v for k, v in self._payload.items() if k != "threshold_value"}
        r = client.post("/threshold", json=incomplete, headers=_auth(admin_token))
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /threshold/{id}
# ---------------------------------------------------------------------------

class TestUpdateThreshold:
    def test_admin_updates_threshold(self, client, admin_token):
        updated = _make_threshold(1, threshold_value=75.0)
        with patch(
            "app.services.threshold_repository.update_threshold",
            return_value=updated,
        ):
            r = client.patch(
                "/threshold/1",
                json={"threshold_value": 75.0},
                headers=_auth(admin_token),
            )
        assert r.status_code == 200
        assert r.json()["threshold_value"] == 75.0

    def test_update_nonexistent_returns_404(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.update_threshold",
            return_value=None,
        ):
            r = client.patch(
                "/threshold/999",
                json={"threshold_value": 10.0},
                headers=_auth(admin_token),
            )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /threshold/{id}/activate  &  /deactivate
# ---------------------------------------------------------------------------

class TestActivateDeactivate:
    def test_activate_threshold(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.set_threshold_active",
            return_value=_make_threshold(1, is_active=True),
        ):
            r = client.patch("/threshold/1/activate", headers=_auth(admin_token))
        assert r.status_code == 200
        assert r.json()["is_active"] is True

    def test_deactivate_threshold(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.set_threshold_active",
            return_value=_make_threshold(1, is_active=False),
        ):
            r = client.patch("/threshold/1/deactivate", headers=_auth(admin_token))
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_activate_nonexistent_returns_404(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.set_threshold_active",
            return_value=None,
        ):
            r = client.patch("/threshold/999/activate", headers=_auth(admin_token))
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /threshold/{id}
# ---------------------------------------------------------------------------

class TestDeleteThreshold:
    def test_admin_deletes_threshold(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.delete_threshold",
            return_value=True,
        ):
            r = client.delete("/threshold/1", headers=_auth(admin_token))
        assert r.status_code == 204
        # 204 No Content must have an empty body — asserting this ensures the
        # response_class=Response fix on the DELETE route is in place.
        assert r.content == b""

    def test_delete_nonexistent_returns_404(self, client, admin_token):
        with patch(
            "app.services.threshold_repository.delete_threshold",
            return_value=False,
        ):
            r = client.delete("/threshold/999", headers=_auth(admin_token))
        assert r.status_code == 404
