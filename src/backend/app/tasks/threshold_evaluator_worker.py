"""Background polling loop for threshold evaluation (FastAPI lifespan).

Simple explanation: A timer that wakes up every few seconds and says “run the checker
again” so new bad readings can become alerts without you clicking anything.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

EVALUATOR_INTERVAL_SECONDS = 5


async def threshold_evaluator_worker() -> None:
    """Run `run_threshold_evaluation_cycle` every few seconds until cancelled."""
    from app.services.threshold_evaluation import run_threshold_evaluation_cycle

    while True:
        try:
            await asyncio.to_thread(run_threshold_evaluation_cycle)
        except Exception:
            logger.exception("Threshold evaluation cycle failed")
        await asyncio.sleep(EVALUATOR_INTERVAL_SECONDS)
