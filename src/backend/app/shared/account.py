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
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.shared.enums import UserRole


class AccountBase(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    role: UserRole
    age: Optional[int] = None
    address: Optional[str] = None
    is_active: bool = True


class AccountCreate(AccountBase):
    password: str = Field(..., min_length=8)


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    age: Optional[int] = None
    address: Optional[str] = None


class AccountPasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class AccountResponse(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account: AccountResponse

