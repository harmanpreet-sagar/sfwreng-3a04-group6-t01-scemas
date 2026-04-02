"""
Account Management router. token verification handled by stub
"""
 
from __future__ import annotations
 
from datetime import datetime
from typing import Optional
 
from fastapi import APIRouter, Depends, HTTPException, Query
 
from app.shared.account import (
    AccountCreate, AccountListResponse, AccountResponse,
    AuditLogListResponse, CredentialsUpdate, LoginRequest, LoginResponse,
)
from app.shared.dependencies import get_current_account, require_admin
from app.services.account_service import AccountService
 
router = APIRouter(prefix="/account", tags=["Account Management"])
 
_NOT_FOUND = "No account with this aid"
 
 
@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    """
    stub; returns identity verified
    """
    result = AccountService.login(body.email, body.password)
    if result is None:
        raise HTTPException(
            status_code=401,
            detail="[POC] Login failed — email or password incorrect, or account inactive.",
        )
    return LoginResponse(message="Identity verified", identity_verified=True, account=result["account"])
 
 
@router.post("/register", response_model=AccountResponse, status_code=201)
def register(
    body: AccountCreate,
    actor: dict = Depends(require_admin),
) -> AccountResponse:
    """admin check is a stub"""
    return AccountService.create_account(data=body, actor_id=actor["aid"], actor_email=actor["email"])
 
 
@router.get("", response_model=AccountListResponse)
def list_accounts(_: dict = Depends(require_admin)) -> AccountListResponse:
    """admin check is a stub"""
    rows = AccountService.list_accounts()
    return AccountListResponse(accounts=rows, total=len(rows))
 
 
@router.get("/audit-log", response_model=AuditLogListResponse)
def get_audit_log(
    event_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    _: dict = Depends(require_admin),
) -> AuditLogListResponse:
    """audit log, admin check is a stub"""
    entries = AccountService.list_audit_log(event_type=event_type, date_from=date_from, date_to=date_to)
    return AuditLogListResponse(entries=entries, total=len(entries))
 
 
@router.get("/{aid}", response_model=AccountResponse)
def get_account(aid: int, current: dict = Depends(get_current_account)) -> AccountResponse:
    """get account by aid, no security measures"""
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
    """identity check is a stub"""
    account = AccountService.change_credentials(aid=aid, new_password=body.new_password, actor_id=current["aid"], actor_email=current["email"],)
    if account is None:
        raise HTTPException(status_code=404, detail={"error": "account_not_found", "message": _NOT_FOUND, "aid": aid})
    return account
 
 
@router.patch("/{aid}/deactivate", response_model=AccountResponse)
def deactivate_account(aid: int, actor: dict = Depends(require_admin)) -> AccountResponse:
    """deactivating account, admin check is a stub"""
    account = AccountService.deactivate_account(aid=aid, actor_id=actor["aid"], actor_email=actor["email"])
    if account is None:
        raise HTTPException(status_code=404, detail={"error": "account_not_found", "message": _NOT_FOUND, "aid": aid})
    return account