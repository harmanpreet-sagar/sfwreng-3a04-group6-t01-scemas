"""
One audit log line per public API HTTP response (success or failure).

Depends on request.state.public_api_key_* set by require_public_api_key after a
successful key lookup; missing key on 401 is expected.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.shared.audit import log_audit_event


def _is_public_api_path(path: str) -> bool:
    return path.startswith("/public/") or path.startswith("/api/public/")


def _outcome_for_status(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "success"
    if status_code == 401:
        return "auth_failed"
    if status_code == 429:
        return "rate_limited"
    if status_code == 404:
        return "not_found"
    if status_code == 422:
        return "validation_error"
    if 400 <= status_code < 500:
        return "client_error"
    if status_code >= 500:
        return "server_error"
    return "unknown"


class PublicApiAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        path = request.url.path
        if not _is_public_api_path(path):
            return response
        if request.method == "OPTIONS":
            return response

        details: dict[str, object] = {
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "outcome": _outcome_for_status(response.status_code),
        }
        key_id = getattr(request.state, "public_api_key_id", None)
        key_label = getattr(request.state, "public_api_key_label", None)
        if key_id is not None:
            details["api_key_id"] = key_id
        if key_label is not None:
            details["api_key_label"] = key_label

        log_audit_event("public_api.request", details=details)
        return response
