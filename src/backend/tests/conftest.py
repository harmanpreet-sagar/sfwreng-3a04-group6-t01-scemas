"""
Shared pytest fixtures.

Sets JWT_SECRET and a fake DB URL before any app module is imported so the
app starts without a real database connection.  Repository calls are patched
per-test in the individual test files.
"""

import asyncio
import os

# These must be set before any app import because several modules (auth.py,
# db.py) read env vars at module load time, not at first call.  Moving these
# lines below the import block would cause RuntimeError / connection failures
# even before a single test function runs.
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest-do-not-use-in-prod")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://fake:fake@localhost:5432/fake")

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


async def _noop_worker() -> None:
    # Sleeps until cancelled rather than returning immediately so it mimics the
    # real worker's lifetime (a long-running coroutine that only stops on app
    # shutdown).  If it returned immediately, the lifespan task would be
    # finished before the test even starts, which could mask cancellation bugs.
    await asyncio.sleep(9999)


@pytest.fixture(scope="session")
def app():
    # scope="session" — one FastAPI app instance is shared across the entire
    # test session, which avoids the overhead of re-importing and re-wiring
    # startup hooks for every test class.
    with (
        patch("app.shared.api_key_seed.seed_demo_public_api_key"),
        patch(
            "app.tasks.threshold_evaluator_worker.threshold_evaluator_worker",
            _noop_worker,
        ),
    ):
        from main import app as fastapi_app  # noqa: PLC0415

        return fastapi_app


@pytest.fixture(scope="session")
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token():
    from app.shared.auth import create_access_token
    from app.shared.enums import UserRole

    return create_access_token(1, "admin@test.com", UserRole.admin)


@pytest.fixture(scope="session")
def operator_token():
    from app.shared.auth import create_access_token
    from app.shared.enums import UserRole

    return create_access_token(2, "operator@test.com", UserRole.operator)
