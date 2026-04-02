"""
Shared pytest fixtures.

Environment variables are set before any app module is imported because auth.py
and db.py read os.getenv() at module load time, not on first call.  Setting them
after the import would cause RuntimeError or connection failures before any test
function runs.

Startup side-effects (DB seeds, background workers) are all patched out so the
test suite can run without a real database or MQTT broker.
"""

import asyncio
import os

# Must come before any `from main import ...` or `from app import ...` call.
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest-do-not-use-in-prod")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://fake:fake@localhost:5432/fake")

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


async def _noop_worker() -> None:
    """
    Stand-in for any long-running async worker (evaluator, MQTT subscriber).

    Sleeps until cancelled rather than returning immediately so it behaves like
    the real workers — a coroutine that lives for the entire app lifespan.
    Returning immediately would finish the asyncio task before the test even
    starts, which could hide bugs in the cancellation/shutdown path.
    """
    await asyncio.sleep(9999)


@pytest.fixture(scope="session")
def app():
    """
    Build a single FastAPI application instance shared across the whole test run.

    scope="session" avoids re-importing and re-wiring the app for every test
    class, which significantly speeds up the suite.

    All four startup side-effects are patched before the import so no real
    I/O occurs:
      seed_demo_public_api_key  — would hit the DB on startup
      seed_default_thresholds   — would hit the DB on startup
      threshold_evaluator_worker — long-running polling loop
      run_mqtt_subscriber        — opens a TLS connection to Mosquitto
    """
    with (
        patch("app.shared.api_key_seed.seed_demo_public_api_key"),
        patch("app.shared.threshold_seed.seed_default_thresholds"),
        patch(
            "app.tasks.threshold_evaluator_worker.threshold_evaluator_worker",
            _noop_worker,
        ),
        patch(
            "app.tasks.mqtt_subscriber.run_mqtt_subscriber",
            _noop_worker,
        ),
    ):
        from main import app as fastapi_app  # noqa: PLC0415
        return fastapi_app


@pytest.fixture(scope="session")
def client(app):
    """
    Provide an HTTPX TestClient that wraps the shared app instance.

    Using a context manager ensures the FastAPI lifespan (startup/shutdown) runs
    exactly once per session, matching production behaviour as closely as possible.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token():
    """
    Return a signed JWT for an admin test account.

    Uses the same create_access_token() function as the real login endpoint so
    the token format is identical to what production callers would receive.
    """
    from app.shared.auth import create_access_token
    from app.shared.enums import UserRole

    return create_access_token(1, "admin@test.com", UserRole.admin)


@pytest.fixture(scope="session")
def operator_token():
    """
    Return a signed JWT for an operator test account.

    Used by tests that verify RBAC boundaries — e.g. confirming that operator
    tokens are rejected on admin-only endpoints with 403.
    """
    from app.shared.auth import create_access_token
    from app.shared.enums import UserRole

    return create_access_token(2, "operator@test.com", UserRole.operator)
