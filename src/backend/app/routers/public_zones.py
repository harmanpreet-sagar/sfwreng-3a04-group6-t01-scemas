"""
Read-only public zone summaries (Deliverable 4).

Requires API key + in-memory rate limit. No per-zone route here.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models.public_zone import PublicZonesListResponse
from app.services.public_zones_service import list_public_zones
from app.shared.deps_public_api import PublicApiKeyRateLimitedDep

router = APIRouter(prefix="/public", tags=["Public API"])


@router.get(
    "/zones",
    response_model=PublicZonesListResponse,
    summary="List zone-level aggregated environmental summaries",
)
def get_public_zones(
    _api_key: PublicApiKeyRateLimitedDep,
) -> PublicZonesListResponse:
    return list_public_zones()
