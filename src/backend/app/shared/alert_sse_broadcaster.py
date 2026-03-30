"""
In-memory SSE fan-out for alert events (proof-of-concept).

Safe to call publish() from sync code (e.g. AlertService); subscribers consume via
async StreamingResponse. Slow clients that fill their queue are dropped.
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from typing import Any, Set

from fastapi import Request

from app.models.alert import AlertResponse

# Event type strings for dashboard routing
ALERT_SSE_CREATED = "alert.created"
ALERT_SSE_ACKNOWLEDGED = "alert.acknowledged"
ALERT_SSE_RESOLVED = "alert.resolved"


def build_alert_sse_event(alert: AlertResponse, event_type: str) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "id": alert.id,
        "status": alert.status.value,
        "severity": alert.severity.value,
        "zone": alert.zone,
        "metric": alert.metric,
        "message": alert.message,
        "observed_value": alert.observed_value,
        "threshold_value": alert.threshold_value,
        "threshold_id": alert.threshold_id,
        "created_at": alert.created_at.isoformat(),
        "updated_at": alert.updated_at.isoformat(),
        "acknowledged_at": (
            alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        ),
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
    }


def publish_alert_sse(alert: AlertResponse, event_type: str) -> None:
    """Publish one event to all connected SSE clients (no-op if none)."""
    alert_sse_broadcaster.publish(build_alert_sse_event(alert, event_type))


class AlertSSEBroadcaster:
    """Thread-safe pub/sub using bounded queues per connected client."""

    KEEPALIVE_SECONDS = 15
    MAX_QUEUE = 50

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queues: Set[queue.Queue] = set()

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=self.MAX_QUEUE)
        with self._lock:
            self._queues.add(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            self._queues.discard(q)

    def publish(self, event: dict[str, Any]) -> None:
        with self._lock:
            subscribers = list(self._queues)
        stale: list[queue.Queue] = []
        for q in subscribers:
            try:
                q.put_nowait(event)
            except queue.Full:
                stale.append(q)
        for q in stale:
            self.unsubscribe(q)

    async def stream(self, request: Request):
        """Async generator of SSE lines (data JSON + periodic keepalive comments)."""
        q = self.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break

                def wait_event() -> Any | None:
                    try:
                        return q.get(timeout=self.KEEPALIVE_SECONDS)
                    except queue.Empty:
                        return None

                event = await asyncio.to_thread(wait_event)
                if event is None:
                    yield ": keepalive\n\n"
                else:
                    yield f"data: {json.dumps(event, default=str)}\n\n"
        finally:
            self.unsubscribe(q)


alert_sse_broadcaster = AlertSSEBroadcaster()
