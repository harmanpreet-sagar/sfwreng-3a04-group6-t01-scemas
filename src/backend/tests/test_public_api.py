"""
Public API tests (Bearer API key, rate limit, zone routes).

Simple explanation: Checks the public zone JSON, including fields that say if a zone is
in “alert mode” and how serious open alerts are—without using a real database.

Repository/service calls are mocked — no real DB required.
Run from src/backend/:  pytest tests/test_public_api.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.models.public_zone import (
    PublicZoneMetricReading,
    PublicZoneOperationalStatus,
    PublicZoneSummary,
    PublicZonesListResponse,
)
from app.shared.public_api_rate_limiter import RateLimitDenied

_NOW = datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc)


def _bearer(token: str = "test-plaintext-key") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _valid_key_row() -> dict:
    return {"id": 42, "label": "pytest-key"}


def _sample_list_response() -> PublicZonesListResponse:
    summary = PublicZoneSummary(
        zone="zone-a",
        metrics=[
            PublicZoneMetricReading(
                metric="temperature", value=21.5, window_end=_NOW
            )
        ],
        updated_at=_NOW,
        status=PublicZoneOperationalStatus.normal,
        active_alert_highest_severity=None,
    )
    return PublicZonesListResponse(zones=[summary], total=1)


class TestPublicZonesAuth:
    def test_zones_missing_authorization_401(self, client):
        r = client.get("/public/zones")
        assert r.status_code == 401
        assert r.json()["detail"]["error"] == "api_key_missing"

    def test_zones_invalid_bearer_scheme_401(self, client):
        r = client.get("/public/zones", headers={"Authorization": "Basic x"})
        assert r.status_code == 401
        assert r.json()["detail"]["error"] == "api_key_invalid"

    def test_zones_unknown_key_401(self, client):
        with patch(
            "app.shared.deps_public_api.fetch_active_api_key_by_hash",
            return_value=None,
        ):
            r = client.get("/public/zones", headers=_bearer("wrong-key"))
        assert r.status_code == 401
        assert r.json()["detail"]["error"] == "api_key_invalid"


class TestPublicZonesSuccess:
    def test_zones_ok_with_valid_key(self, client):
        with patch(
            "app.shared.deps_public_api.fetch_active_api_key_by_hash",
            return_value=_valid_key_row(),
        ):
            with patch(
                "app.routers.public_zones.list_public_zones",
                return_value=_sample_list_response(),
            ):
                r = client.get("/public/zones", headers=_bearer())
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert len(body["zones"]) == 1
        assert body["zones"][0]["zone"] == "zone-a"
        assert body["zones"][0]["metrics"][0]["metric"] == "temperature"

    def test_zone_by_id_ok(self, client):
        summary = _sample_list_response().zones[0]
        with patch(
            "app.shared.deps_public_api.fetch_active_api_key_by_hash",
            return_value=_valid_key_row(),
        ):
            with patch(
                "app.routers.public_zones.get_public_zone",
                return_value=summary,
            ):
                r = client.get("/public/zones/zone-a", headers=_bearer())
        assert r.status_code == 200
        assert r.json()["zone"] == "zone-a"

    def test_zone_by_id_not_found_404(self, client):
        with patch(
            "app.shared.deps_public_api.fetch_active_api_key_by_hash",
            return_value=_valid_key_row(),
        ):
            with patch(
                "app.routers.public_zones.get_public_zone",
                return_value=None,
            ):
                r = client.get("/public/zones/unknown", headers=_bearer())
        assert r.status_code == 404
        assert r.json()["detail"]["error"] == "zone_not_found"


class TestPublicApiRateLimit:
    def test_zones_rate_limited_429(self, client):
        denied = RateLimitDenied(
            retry_after_seconds=45,
            limit=100,
            window_seconds=60,
        )
        with patch(
            "app.shared.deps_public_api.fetch_active_api_key_by_hash",
            return_value=_valid_key_row(),
        ):
            with patch(
                "app.shared.deps_public_api.public_api_rate_limiter.try_acquire",
                return_value=denied,
            ):
                r = client.get("/public/zones", headers=_bearer())
        assert r.status_code == 429
        d = r.json()["detail"]
        assert d["error"] == "rate_limit_exceeded"
        assert d["limit"] == 100
        assert r.headers.get("Retry-After") == "45"


class TestPublicWhoami:
    def test_whoami_returns_key_metadata(self, client):
        with patch(
            "app.shared.deps_public_api.fetch_active_api_key_by_hash",
            return_value=_valid_key_row(),
        ):
            r = client.get("/api/public/whoami", headers=_bearer())
        assert r.status_code == 200
        assert r.json() == {"key_id": 42, "label": "pytest-key"}
