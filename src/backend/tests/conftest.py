"""
Shared pytest fixtures.

Sets JWT_SECRET and a fake DB URL before any app module is imported so the
app starts without a real database connection.  Repository calls are patched
per-test in the individual test files.
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock

# These must be set before any app import because several modules (auth.py,
# db.py) read env vars at module load time, not at first call.  Moving these
# lines below the import block would cause RuntimeError / connection failures
# even before a single test function runs.
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest-do-not-use-in-prod")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://fake:fake@localhost:5432/fake")

# Some modules only exist on certain branches.  Pre-injecting a MagicMock into
# sys.modules means patch() always has a target regardless of which branch CI
# is running.  When the real file IS present on this branch, __import__ succeeds
# and the real module is used instead.
_OPTIONAL_MODULES = [
    "app.shared.threshold_seed",   # harman branch — default threshold seeding
    "app.shared.seed_accounts",    # jason branch  — demo account seeding
    "app.tasks.mqtt_subscriber",   # ali branch    — MQTT background worker
]
for _mod in _OPTIONAL_MODULES:
    try:
        __import__(_mod)
    except ImportError:
        sys.modules[_mod] = MagicMock()

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


async def _noop_worker() -> None:
    # Sleeps until cancelled rather than returning immediately so it mimics the
    # real worker's lifetime (a long-running coroutine that only stops on app
    # shutdown).  If it returned immediately, the lifespan task would be
    # finished before the test even starts, which could mask cancellation bugs.
    await asyncio.sleep(9999)


@pytest.fixture(scope="session", autouse=True)
def _patch_startup_functions():
    """Hold all startup-side-effect patches open for the entire test session.

    The patches must outlive the `app` fixture because FastAPI's lifespan
    (where seeds and workers are actually called) only runs when TestClient
    enters its context manager — which happens in the `client` fixture, after
    `app` has already returned.  A plain `with patch(...)` inside `app` would
    exit before the lifespan ever fires.

    Patched side-effects:
      seed_demo_public_api_key   — would hit the DB
      seed_default_thresholds    — would hit the DB (harman branch)
      seed_demo_accounts         — would hit the DB (jason branch)
      threshold_evaluator_worker — long-running polling loop
      run_mqtt_subscriber        — opens a TLS connection to Mosquitto (ali branch)
    """
    with (
        patch("app.shared.api_key_seed.seed_demo_public_api_key"),
        patch("app.shared.threshold_seed.seed_default_thresholds"),
        patch("app.shared.seed_accounts.seed_demo_accounts"),
        patch(
            "app.tasks.threshold_evaluator_worker.threshold_evaluator_worker",
            _noop_worker,
        ),
        patch(
            "app.tasks.mqtt_subscriber.run_mqtt_subscriber",
            _noop_worker,
        ),
    ):
        yield  # patches stay active until the very end of the test session


@pytest.fixture(scope="session")
def app(_patch_startup_functions):
    # scope="session" — one FastAPI app instance is shared across the entire
    # test session, which avoids the overhead of re-importing and re-wiring
    # startup hooks for every test class.
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
