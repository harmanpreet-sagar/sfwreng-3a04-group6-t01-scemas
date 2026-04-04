"""
Pydantic models for the Account Management subsystem (Jason).

Schema note — naming mismatch between the class diagram and the DB:
  Class diagram uses `id: int` and `role: UserRole`.
  Jason's DB migration (019_create_accounts.sql) uses `aid` and `clearance: str`.
  These models match the DB schema so nothing breaks at query time.
  When Jason's accounts PR is merged his AccountResponse will replace the one
  below. The extra models (AccountListResponse, CredentialsUpdate, AuditLogEntry,
  AuditLogListResponse) arrive with his PR; they are defined here now so other
  subsystems can import from a stable location without depending on Jason's branch.

JWT integration (added in this PR):
  LoginResponse was extended with `access_token` and `token_type` so the frontend
  can receive a signed JWT in the same response as the account profile. The token
  is optional (None) when JWT_SECRET is not set in the environment — the backend
  degrades gracefully, but all subsequent authenticated requests will fail with 401.
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
