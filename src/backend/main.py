"""
Main FastAPI application entry point for the Threshold Management System.
This module initializes the API Facade layer that routes requests to subsystem services.
"""

import asyncio
import contextlib
from contextlib import asynccontextmanager

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.shared.public_api_audit_middleware import PublicApiAuditMiddleware
from app.routers import alerts as alerts_router
from app.routers import validation as validation_router
from app.routers import public_demo as public_demo_router
from app.routers import public_zones as public_zones_router
from app.routers import thresholds as thresholds_router

# Load environment variables: prefer src/.env when running from src/backend (local dev)
_backend_dir = Path(__file__).resolve().parent
_src_env = _backend_dir.parent / ".env"
load_dotenv(_src_env)
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run one-time startup tasks (e.g. idempotent DB seeds) and background jobs."""
    from app.shared.api_key_seed import seed_demo_public_api_key
    from app.tasks.threshold_evaluator_worker import threshold_evaluator_worker
    from app.tasks.mqtt_subscriber import run_mqtt_subscriber

    seed_demo_public_api_key()
    evaluator_task = asyncio.create_task(threshold_evaluator_worker())
    mqtt_task = asyncio.create_task(run_mqtt_subscriber())
    try:
        yield
    finally:
        evaluator_task.cancel()
        mqtt_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await evaluator_task
        with contextlib.suppress(asyncio.CancelledError):
            await mqtt_task


# Initialize FastAPI application with OpenAPI documentation metadata
app = FastAPI(
    title="SFWRENG 3A04 - Group 6 API",
    description="Backend API for Threshold Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS to allow frontend (running on different port/domain) to make requests
# TODO: Restrict allow_origins to specific domains in production for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PublicApiAuditMiddleware)

app.include_router(alerts_router.router)
app.include_router(validation_router.router)
app.include_router(thresholds_router.router)
app.include_router(public_demo_router.router)
app.include_router(public_zones_router.router)


@app.get("/")
async def root():
    """Root endpoint for basic API verification."""
    return {"message": "Welcome to Group 6 API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration and monitoring."""
    return {"status": "healthy"}


# Direct execution entry point for local development without Docker
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

