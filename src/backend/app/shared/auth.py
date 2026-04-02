"""
JWT authentication and RBAC middleware for FastAPI route protection.

Usage in route handlers:
    from app.shared.auth import require_admin, require_operator_or_admin, CurrentUser

    @router.post("/thing")
    def create_thing(payload: ..., user: CurrentUser = Depends(require_admin)):
        ...  # user.account_id, user.email, user.role are available

JWT payload shape (agreed with Jason's login endpoint):
    { "sub": "<account_id>", "email": "<email>", "role": "ADMIN" | "OPERATOR" }
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.shared.enums import UserRole

_bearer = HTTPBearer(auto_error=False)
_ALGORITHM = "HS256"


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET env var is not set")
    return secret


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _get_jwt_secret(), algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


class CurrentUser:
    """Parsed JWT claims attached to a request."""

    def __init__(self, account_id: int, email: str, role: UserRole) -> None:
        self.account_id = account_id
        self.email = email
        self.role = role


def _extract_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_token",
                "message": "Authorization: Bearer <token> header is required",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_token(credentials.credentials)
    try:
        return CurrentUser(
            account_id=int(payload["sub"]),
            email=str(payload["email"]),
            role=UserRole(payload["role"]),
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "malformed_token",
                "message": "Token is missing required claims (sub, email, role)",
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_admin(user: CurrentUser = Depends(_extract_user)) -> CurrentUser:
    """FastAPI Depends — rejects any non-ADMIN caller with 403."""
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": "This action requires ADMIN role",
                "your_role": user.role.value,
            },
        )
    return user


def require_operator_or_admin(user: CurrentUser = Depends(_extract_user)) -> CurrentUser:
    """FastAPI Depends — allows OPERATOR and ADMIN; rejects everything else with 403."""
    if user.role not in (UserRole.admin, UserRole.operator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": "This action requires OPERATOR or ADMIN role",
                "your_role": user.role.value,
            },
        )
    return user


def create_access_token(account_id: int, email: str, role: UserRole) -> str:
    """
    Sign and return a JWT. Called by Jason's POST /account/login endpoint.

    Example:
        token = create_access_token(account.id, account.email, account.role)
        return LoginResponse(access_token=token, account=account_response)
    """
    payload = {"sub": str(account_id), "email": email, "role": role.value}
    return jwt.encode(payload, _get_jwt_secret(), algorithm=_ALGORITHM)
