"""
JWT authentication and RBAC middleware for FastAPI route protection.

All protected routes should depend on require_admin or require_operator_or_admin
rather than calling _extract_user directly.  This guarantees the RBAC gate is
never accidentally skipped.

Usage in route handlers:
    from app.shared.auth import require_admin, require_operator_or_admin, CurrentUser

    @router.post("/thing")
    def create_thing(payload: ..., user: CurrentUser = Depends(require_admin)):
        ...  # user.account_id, user.email, user.role are available

JWT payload shape (must match POST /account/login):
    { "sub": "<account_id>", "email": "<email>", "role": "ADMIN" | "OPERATOR" }

Algorithm: HS256 (symmetric).  Secret read from JWT_SECRET env var at call time
so a key rotation only requires an env change and a restart.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.shared.enums import UserRole

# auto_error=False lets us return a structured JSON 401 on a missing
# Authorization header instead of FastAPI's default plain-text
# "Not authenticated" response, which is harder for clients to parse.
_bearer = HTTPBearer(auto_error=False)
_ALGORITHM = "HS256"


def _get_jwt_secret() -> str:
    """
    Read JWT_SECRET from the environment at call time (not at import time).

    Delaying the read means tests can patch os.environ after module import,
    and a running server can detect a missing secret as soon as the first
    protected request arrives rather than silently using an empty string.
    """
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET env var is not set")
    return secret


def _decode_token(token: str) -> dict:
    """
    Verify the token signature and return its claims dict.

    Raises HTTP 401 if the token is expired, tampered with, or otherwise
    invalid.  python-jose's jwt.decode() handles all cryptographic checks
    including algorithm enforcement (HS256 only) to prevent algorithm
    confusion attacks.
    """
    try:
        return jwt.decode(token, _get_jwt_secret(), algorithms=[_ALGORITHM])
    except JWTError as exc:
        logger.warning("[AUTH DEBUG] 401: invalid_token — %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


class CurrentUser:
    """
    Parsed JWT claims attached to a request after successful authentication.

    account_id and email come from the `sub` and `email` JWT claims.
    role is the Python enum equivalent of the `role` string claim so route
    handlers can compare against UserRole.admin / UserRole.operator directly.
    """

    def __init__(self, account_id: int, email: str, role: UserRole) -> None:
        self.account_id = account_id
        self.email = email
        self.role = role


# _extract_user is intentionally private — it provides a raw CurrentUser with
# no role enforcement.  Route handlers must always use require_admin or
# require_operator_or_admin so the RBAC gate cannot be accidentally bypassed.
def _extract_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> CurrentUser:
    """
    Extract and validate claims from the Bearer token.

    Raises 401 if:
      - the Authorization header is absent
      - the token signature is invalid or expired
      - the token is missing required claims (sub, email, role)

    sub is a string per RFC 7519, so it is explicitly cast to int since the
    DB stores account ids as integers.
    """
    if credentials is None:
        logger.warning("[AUTH DEBUG] 401: missing Authorization header entirely")
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
        # KeyError  → a required claim is absent from the payload
        # ValueError → role string does not match any UserRole enum member
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "malformed_token",
                "message": "Token is missing required claims (sub, email, role)",
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_admin(user: CurrentUser = Depends(_extract_user)) -> CurrentUser:
    """
    FastAPI Depends — rejects any non-ADMIN caller with 403.

    Compose this into route handlers that should only be accessible to
    administrators (e.g. creating, updating, or deleting thresholds).
    """
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
    """
    FastAPI Depends — allows OPERATOR and ADMIN; rejects anything else with 403.

    Use for read-heavy endpoints where both roles need access
    (e.g. listing thresholds, reading alerts).
    """
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
    Sign and return a JWT.  Call from POST /account/login after credential check.

    The payload carries the three claims that _extract_user expects: sub, email,
    and role.  Tokens have no exp claim for this PoC sprint — add expiry and a
    refresh-token endpoint before any production deployment.

    Example:
        token = create_access_token(account.id, account.email, account.role)
        return LoginResponse(access_token=token, account=account_response)
    """
    payload = {"sub": str(account_id), "email": email, "role": role.value}
    return jwt.encode(payload, _get_jwt_secret(), algorithm=_ALGORITHM)
