"""Validated public API key identity (for logging / future rate limits)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PublicApiKeyAuth(BaseModel):
    """Row subset from `api_keys` after successful validation."""

    id: int = Field(..., description="Primary key in api_keys")
    label: str = Field(..., description="Human-readable key label")
