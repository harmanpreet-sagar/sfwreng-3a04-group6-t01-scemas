"""
Read-only public zone summaries (Deliverable 4).

Requires API key + in-memory rate limit.

Simple explanation: Public URLs that return zone summaries, including a simple alerting
hint (normal vs alerting) derived from active alerts—needs an API key like a badge.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from app.models.public_zone import PublicZoneSummary, PublicZonesListResponse
from app.services.public_zones_service import get_public_zone, list_public_zones
from app.shared.deps_public_api import PublicApiKeyRateLimitedDep
from app.shared.public_api_errors import public_api_error_payload

router = APIRouter(prefix="/public", tags=["Public API"])

_ZONE_PATH = Path(
    ...,
    min_length=1,
    max_length=256,
    description="Zone identifier (must match values stored in aggregated_data)",
)


@router.get(
    "/zones",
    response_model=PublicZonesListResponse,
    summary="List zone-level aggregated environmental summaries",
)
def get_public_zones(
    _api_key: PublicApiKeyRateLimitedDep,
) -> PublicZonesListResponse:
    return list_public_zones()


@router.get(
    "/zones/{zone}",
    response_model=PublicZoneSummary,
    summary="Get aggregated environmental summary for one zone",
)
def get_public_zone_by_id(
    _api_key: PublicApiKeyRateLimitedDep,
    zone: Annotated[str, _ZONE_PATH],
) -> PublicZoneSummary:
    z = zone.strip()
    if not z:
        raise HTTPException(
            status_code=422,
            detail=public_api_error_payload(
                error="invalid_zone",
                message=(
                    "Zone path must be a non-empty identifier after trimming whitespace."
                ),
            ),
        )
    summary = get_public_zone(z)
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail=public_api_error_payload(
                error="zone_not_found",
                message="No aggregated data exists for this zone.",
                zone=z,
            ),
        )
    return summary
