"""
Pydantic models for the Account Management subsystem (Jason).

Our class-diagram schema uses `id` and `role: UserRole`.
Jason's DB schema uses `aid` and `clearance: str`.

When Jason's accounts PR is merged his AccountResponse (aid/clearance) will
replace the one below.  Until then these models serve as the API contract so
nothing in the shared layer breaks.  Classes that Jason's router needs but
that don't exist here yet (AccountListResponse, CredentialsUpdate,
AuditLogEntry, AuditLogListResponse) will arrive with his PR.
"""

from __future__ import annotations
 
from datetime import datetime
from typing import List, Optional
 
from pydantic import BaseModel, EmailStr, Field
 
 
class AccountResponse(BaseModel):
    aid: int
    name: str
    email: str
    clearance: str
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
    clearance: str = Field(..., pattern="^(admin|operator)$")
 
 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
 
 
class LoginResponse(BaseModel):
    """
    POC login response, verified by stub
    """
    message: str
    identity_verified: bool
    account: AccountResponse

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

