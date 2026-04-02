"""
API Facade — main FastAPI application entry point.

This module is the single place where every subsystem router is registered.
It owns startup lifecycle (seeds + background workers) and middleware.

Two registration strategies are used:
  Hard imports   — routers that are fully merged and must always load.
                   Import errors surface immediately in CI.
  _try_include_router() — routers whose branch has not yet merged.
                          A missing file logs a warning but never crashes the app.
                          No changes to this file are needed when the PR lands.

Wiring status
  alerts       ✓ merged (Harmanpreet)
  thresholds   ✓ merged (Harmanpreet)
  validation   ✓ merged (Ali)
  public        ✓ merged (Harmanpreet)
  accounts     ⏳ waiting for Jason's PR  (app/routers/accounts.py)
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# .env must be loaded before any app module reads os.getenv() at import time.
# We try src/.env first (used when running from src/backend/ locally) then
# fall back to whatever load_dotenv() finds in the current working directory.
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir.parent / ".env")
load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context — runs once on startup, tears down on shutdown.

    Seeds are imported inside the context (not at module level) so they are
    only executed when the real app starts, not when pytest imports main.py
    for test collection.  conftest.py patches them before the import anyway,
    but the lazy import is an extra safety net.

    Workers are created as asyncio tasks so they run concurrently with request
    handling.  The finally block cancels and awaits each task so in-flight work
    is drained before the process exits.
    """
    from app.shared.api_key_seed import seed_demo_public_api_key
    from app.shared.threshold_seed import seed_default_thresholds
    from app.tasks.threshold_evaluator_worker import threshold_evaluator_worker
    from app.tasks.mqtt_subscriber import run_mqtt_subscriber

    # Idempotent seeds — safe to run on every restart; they check for existing
    # data before inserting so they never overwrite operator-configured state.
    seed_demo_public_api_key()
    seed_default_thresholds()

    evaluator_task = asyncio.create_task(threshold_evaluator_worker())
    mqtt_task      = asyncio.create_task(run_mqtt_subscriber())

    try:
        yield
    finally:
        # Cancel both tasks together then await them individually so neither
        # blocks the other from receiving its CancelledError.
        for t in (evaluator_task, mqtt_task):
            t.cancel()
        for t in (evaluator_task, mqtt_task):
            with contextlib.suppress(asyncio.CancelledError):
                await t


app = FastAPI(
    title="SFWRENG 3A04 — Group 6 API",
    description=(
        "Backend API Facade for the SCEMAS Threshold Management System.\n\n"
        "**Subsystems:**\n"
        "- Alerts (Harmanpreet)\n"
        "- Threshold Management (Harmanpreet)\n"
        "- Data Validation (Ali)\n"
        "- Account Management (Jason) — pending PR merge\n"
        "- Public API (Harmanpreet)\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS is wide-open for the PoC sprint so the React frontend on a different
# port can reach the API without preflight failures.
# TODO: narrow allow_origins to the actual frontend domain before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logs the API key label on every /public/* request for audit purposes.
# Must be added after CORSMiddleware so it runs inside the CORS layer.
from app.shared.public_api_audit_middleware import PublicApiAuditMiddleware
app.add_middleware(PublicApiAuditMiddleware)


# ── Utility: safe registration for not-yet-merged routers ─────────────────────

def _try_include_router(module_path: str, label: str) -> None:
    """
    Attempt to import module_path and register its router attribute.

    On ImportError (file not on disk yet, or a dependency missing) the router
    is skipped and a warning is logged — the rest of the app continues running
    normally.  When the teammate's PR finally merges, their file appears on disk
    and the router registers automatically on the next server restart with no
    changes needed here.

    A broad Exception catch is also present so an unexpected error in a
    teammate's module-level code (e.g. a syntax error) produces a clear log
    entry rather than an unhandled exception that kills the whole process.
    """
    try:
        mod = importlib.import_module(module_path)
        app.include_router(mod.router)
        logger.info("Router registered: %s", label)
    except ImportError as exc:
        logger.warning("%-25s router skipped — import failed: %s", label, exc)
    except Exception as exc:
        logger.error("%-25s router failed: %s", label, exc, exc_info=True)


# ── Merged routers — hard imports (CI catches any breakage immediately) ────────
from app.routers import alerts       as alerts_router
from app.routers import thresholds   as thresholds_router
from app.routers import validation   as validation_router
from app.routers import public_demo  as public_demo_router
from app.routers import public_zones as public_zones_router

app.include_router(alerts_router.router)
app.include_router(thresholds_router.router)
app.include_router(validation_router.router)
app.include_router(public_demo_router.router)
app.include_router(public_zones_router.router)

# ── Pending routers — auto-activate the moment the PR is merged ───────────────
_try_include_router("app.routers.accounts", "Account Management")   # Jason


# ── Utility endpoints ──────────────────────────────────────────────────────────

@app.get("/", tags=["Meta"])
async def root():
    """Root endpoint — quick smoke-test that the server is reachable."""
    return {"message": "Welcome to Group 6 API"}


@app.get("/health", tags=["Meta"])
async def health_check():
    """
    Health check for Docker / container orchestration.
    Returns 200 as long as the process is alive — does not probe the DB
    so a slow Supabase connection never causes a false-positive unhealthy status.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
