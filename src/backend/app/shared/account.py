"""
Pydantic models for account management.

Naming follows the DB (see migration 019_create_accounts.sql): primary key `aid`,
clearance string `clearance` ("admin" | "operator"), not diagram-style `id` + enum role.

LoginResponse includes optional `access_token` / `token_type` so the client gets
a JWT alongside the profile. If JWT_SECRET is unset, the token is omitted and
protected routes return 401 until configured.
"""

from __future__ import annotations
 
from datetime import datetime
from typing import List, Optional
 
from pydantic import BaseModel, EmailStr, Field
 
 
class AccountResponse(BaseModel):
    aid: int
    name: str
    email: str
    clearance: str          # "admin" | "operator" — lowercase, matches the DB column
    is_active: bool
    created_at: datetime
    updated_at: datetime
 
    model_config = {"from_attributes": True}
 
 
class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int
 
 
class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
    # Pattern enforces the two valid clearance values; the backend never stores
    # arbitrary strings in this column.
    clearance: str = Field(..., pattern="^(admin|operator)$")
 
 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
 
 
class LoginResponse(BaseModel):
    """
    Login response — returned by POST /account/login.

    access_token is a signed HS256 JWT (see app/shared/auth.py). It is absent
    (None) only if JWT_SECRET is not configured in the backend environment.
    The frontend attaches this token as `Authorization: Bearer <token>` on all
    subsequent requests to protected endpoints (thresholds CRUD, etc.).
    token_type is always "bearer" per RFC 6750.
    """
    message: str
    identity_verified: bool
    account: AccountResponse
    access_token: Optional[str] = None
    token_type: str = "bearer"


class CredentialsUpdate(BaseModel):
    new_password: str = Field(..., min_length=1, max_length=128)


class AuditLogEntry(BaseModel):
    id: int
    event_type: str
    actor_id: Optional[int]
    actor_email: Optional[str]
    target_id: Optional[int]
    target_email: Optional[str]
    detail: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    entries: List[AuditLogEntry]
    total: int

class PendingRequestCreate(BaseModel):
    """Body for POST /account/request"""
    name: str = Field(..., min_length=1, max_length=128)
    email: EmailStr
    clearance: str = Field(..., pattern="^(admin|operator)$")
    reason: Optional[str] = Field(None, max_length=500)
 
 
class PendingRequestResponse(BaseModel):
    id: int
    name: str
    email: str
    clearance: str
    reason: Optional[str]
    requested_at: datetime
 
    model_config = {"from_attributes": True}
 
 
class PendingRequestListResponse(BaseModel):
    requests: List[PendingRequestResponse]
    total: int
 
