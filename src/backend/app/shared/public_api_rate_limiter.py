"""
In-memory sliding-window rate limiter for the public API (per api_keys.id).

PoC: no Redis; safe enough for demo/dev with a process-wide lock.
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional

# Deliverable 4: 100 requests per minute per API key
PUBLIC_API_RATE_LIMIT = 100
PUBLIC_API_RATE_WINDOW_SECONDS = 60


@dataclass(frozen=True)
class RateLimitDenied:
    """Returned when a request would exceed the limit (caller maps to HTTP 429)."""

    retry_after_seconds: int
    limit: int
    window_seconds: int


class PublicApiRateLimiter:
    """
    Sliding window: keep request timestamps per key; drop entries older than window.
    """

    def __init__(
        self,
        *,
        max_requests: int = PUBLIC_API_RATE_LIMIT,
        window_seconds: float = PUBLIC_API_RATE_WINDOW_SECONDS,
    ) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._lock = threading.Lock()
        self._timestamps: Dict[int, Deque[float]] = {}

    def try_acquire(self, api_key_id: int) -> Optional[RateLimitDenied]:
        """
        If under the limit, record this request and return None.
        If over the limit, return RateLimitDenied (request is not counted).
        """
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            dq = self._timestamps.get(api_key_id)
            if dq is None:
                dq = deque()
                self._timestamps[api_key_id] = dq
            while dq and dq[0] <= cutoff:
                dq.popleft()
            if len(dq) >= self._max:
                wait = dq[0] + self._window - now
                retry = max(1, int(math.ceil(wait)))
                return RateLimitDenied(
                    retry_after_seconds=retry,
                    limit=self._max,
                    window_seconds=int(self._window),
                )
            dq.append(now)
        return None


public_api_rate_limiter = PublicApiRateLimiter()
