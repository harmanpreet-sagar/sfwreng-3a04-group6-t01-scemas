"""
Account Management router.

JWT integration (added in this PR):
  The login endpoint was extended to issue a signed JWT after successful
  credential verification. Previously it returned only the account profile,
  which meant the frontend had no token to attach to threshold API calls
  protected by get_current_user_token() in app/shared/auth.py.

  The JWT payload contains account_id, email, and role. Role is derived by
  uppercasing the DB clearance string ("admin" → "ADMIN") to match the UserRole
  enum expected by create_access_token(). If the clearance value is unrecognised,
  we fall back to UserRole.operator rather than raising — prefer least privilege
  over a hard failure at login time.

  If JWT_SECRET is not set in the environment, create_access_token() raises
  RuntimeError. We catch it and log a warning rather than returning a 500 so
  the user still gets the account profile (useful for debugging), even though
  they won't be able to access protected endpoints.

Token security:
  - Tokens are signed with HS256 using the JWT_SECRET environment variable.
  - Expiry is set in app/shared/auth.py (default 60 minutes).
  - There is no refresh token mechanism; after expiry the user must re-login.
    This is acceptable for a demo with short sessions.

Dependency stubs:
  get_current_account and require_admin use account_dependencies.py (header-based
  PoC). Production flows should use shared/auth.py JWT dependencies instead.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.shared.account import (
    AccountCreate, AccountListResponse, AccountResponse,
    AuditLogListResponse, CredentialsUpdate, LoginRequest, LoginResponse,

    PendingRequestCreate,
    PendingRequestListResponse,
    PendingRequestResponse,
)
from app.shared.account_dependencies import get_current_account, require_admin
from app.services.accounts_service import AccountService
from app.shared.enums import UserRole
from app.shared.auth import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["Account Management"])

_NOT_FOUND = "No account with this aid"


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    """
    Authenticate with email + password.

    Returns the full account profile and a signed JWT (access_token) if
    JWT_SECRET is configured. The frontend must include this token as
    `Authorization: Bearer <token>` on all subsequent requests to protected
    routes (e.g. threshold CRUD, account management).

    Returns HTTP 401 if the email does not exist, the password is wrong,
    or the account is inactive (is_active = FALSE in the DB).
    """
    result = AccountService.login(body.email, body.password)
    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Login failed — email or password incorrect, or account inactive.",
        )
    account = result["account"]

    # Map DB clearance ("admin" / "operator") to the UserRole enum ("ADMIN" / "OPERATOR")
    # expected by create_access_token. The DB stores lowercase; the enum uses uppercase.
    # Unknown clearance values fall back to operator (least privilege).
    try:
        user_role = UserRole(account.clearance.upper())
    except ValueError:
        user_role = UserRole.operator

    token: Optional[str] = None
    try:
        token = create_access_token(
            account_id=account.aid,
            email=account.email,
            role=user_role,
        )
    except RuntimeError:
        # JWT_SECRET is missing from the environment. The login response still
        # includes the account profile so the frontend can surface a useful error
        # rather than a generic 500. All subsequent protected API calls will 401.
        logger.warning("JWT_SECRET not set — login response will not include access_token")

    return LoginResponse(
        message="Identity verified",
        identity_verified=True,
        account=result["account"],
        access_token=token,
    )


@router.post("/register", response_model=AccountResponse, status_code=201)
def register(
    body: AccountCreate,
    actor: dict = Depends(require_admin),
) -> AccountResponse:
    """Create a new account. Requires admin clearance (stub check)."""
    return AccountService.create_account(data=body, actor_id=actor["aid"], actor_email=actor["email"])


@router.get("", response_model=AccountListResponse)
def list_accounts(_: dict = Depends(require_admin)) -> AccountListResponse:
    """List all accounts. Requires admin clearance (stub check)."""
    rows = AccountService.list_accounts()
    return AccountListResponse(accounts=rows, total=len(rows))


@router.get("/audit-log", response_model=AuditLogListResponse)
def get_audit_log(
    event_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    _: dict = Depends(require_admin),
) -> AuditLogListResponse:
    """Retrieve filtered audit log entries. Requires admin clearance (stub check)."""
    entries = AccountService.list_audit_log(event_type=event_type, date_from=date_from, date_to=date_to)
    return AuditLogListResponse(entries=entries, total=len(entries))

@router.post("/request", response_model=PendingRequestResponse, status_code=201)
def submit_request(body: PendingRequestCreate) -> PendingRequestResponse:
    """
    Submit a new account registration request. No auth required — public endpoint.
    The request is stored and surfaced to admins in the pending requests tab.
    """
    try:
        result = AccountService.submit_registration_request(body)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return PendingRequestResponse(**result)
 
 
@router.get("/requests/pending", response_model=PendingRequestListResponse)
def list_pending_requests(_: dict = Depends(require_admin)) -> PendingRequestListResponse:
    """List all pending registration requests. Admin only."""
    rows = AccountService.list_pending_requests()
    return PendingRequestListResponse(requests=[PendingRequestResponse(**r) for r in rows],total=len(rows))
 
 
@router.post("/requests/{request_id}/approve", response_model=AccountResponse)
def approve_request(
    request_id: int,
    actor: dict = Depends(require_admin),
) -> AccountResponse:
    """
    Approve a pending request — creates the account and logs the event.
    Admin only.
    """
    account = AccountService.approve_request(
        request_id=request_id,
        actor_id=actor["aid"],
        actor_email=actor["email"],
    )
    if account is None:
        raise HTTPException(status_code=404,detail={"error": "request_not_found", "message": "No pending request with this id", "request_id": request_id})
    return account
 
 
@router.post("/requests/{request_id}/deny", status_code=200)
def deny_request(
    request_id: int,
    actor: dict = Depends(require_admin),
) -> None:
    """
    Deny a pending request — deletes it and logs the event.
    Admin only.
    """
    deleted = AccountService.deny_request(
        request_id=request_id,
        actor_id=actor["aid"],
        actor_email=actor["email"],
    )
    if not deleted:
        raise HTTPException(status_code=404,detail={"error": "request_not_found", "message": "No pending request with this id", "request_id": request_id})
    return {"message": "Request denied successfully"}


@router.get("/{aid}", response_model=AccountResponse)
def get_account(aid: int, current: dict = Depends(get_current_account)) -> AccountResponse:
    """Get a single account by its primary key (aid)."""
    account = AccountService.get_account_by_id(aid)
    if account is None:
        raise HTTPException(status_code=404, detail={"error": "account_not_found", "message": _NOT_FOUND, "aid": aid})
    return account


@router.patch("/{aid}/credentials", response_model=AccountResponse)
def change_credentials(
    aid: int,
    body: CredentialsUpdate,
    current: dict = Depends(get_current_account),
) -> AccountResponse:
    """Change the password for an account. Identity check is a stub."""
    account = AccountService.change_credentials(
        aid=aid,
        new_password=body.new_password,
        actor_id=current["aid"],
        actor_email=current["email"],
    )
    if account is None:
        raise HTTPException(status_code=404, detail={"error": "account_not_found", "message": _NOT_FOUND, "aid": aid})
    return account
 


@router.patch("/{aid}/deactivate", response_model=AccountResponse)
def deactivate_account(aid: int, actor: dict = Depends(require_admin)) -> AccountResponse:
    """Set is_active = FALSE for an account. Requires admin clearance (stub check)."""
    account = AccountService.deactivate_account(aid=aid, actor_id=actor["aid"], actor_email=actor["email"])
    if account is None:
        raise HTTPException(status_code=404, detail={"error": "account_not_found", "message": _NOT_FOUND, "aid": aid})
    return account
