"""Request-size, rate, and concurrency policy hooks (TRD-API-007, TRD-ING-002)."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass

from memdot_domain.ingestion import IngestionLimits

from memdot_core.errors import ErrorCode, problem_response


@dataclass
class RateBucket:
    count: int
    window_start: float


class InMemoryRateLimiter:
    """Process-local limiter for tests and single-node dev."""

    def __init__(self, *, limit: int = 120, window_seconds: float = 60.0) -> None:
        self._limit = limit
        self._window = window_seconds
        self._buckets: dict[str, RateBucket] = defaultdict(
            lambda: RateBucket(count=0, window_start=time.monotonic())
        )

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._buckets[key]
        if now - bucket.window_start >= self._window:
            bucket.count = 0
            bucket.window_start = now
        if bucket.count >= self._limit:
            return False
        bucket.count += 1
        return True


class ConcurrencyTracker:
    def __init__(self, *, max_active: int) -> None:
        self._max = max_active
        self._active: dict[str, int] = defaultdict(int)

    def try_acquire(self, key: str) -> bool:
        if self._active[key] >= self._max:
            return False
        self._active[key] += 1
        return True

    def release(self, key: str) -> None:
        if self._active[key] > 0:
            self._active[key] -= 1


DEFAULT_LIMITS = IngestionLimits()
GLOBAL_RATE_LIMITER = InMemoryRateLimiter()
PARSE_CONCURRENCY = ConcurrencyTracker(max_active=DEFAULT_LIMITS.max_active_parse_workflows)


def rate_limited_response(*, correlation_id: uuid.UUID | None = None):
    return problem_response(
        status=429,
        code=ErrorCode.RATE_LIMITED,
        detail="Too many requests. Retry later.",
        correlation_id=correlation_id,
    )


def concurrency_limited_response(*, correlation_id: uuid.UUID | None = None):
    return problem_response(
        status=429,
        code=ErrorCode.CONCURRENCY_LIMIT,
        detail="Too many concurrent operations for this account.",
        correlation_id=correlation_id,
    )


def payload_too_large_response(*, correlation_id: uuid.UUID | None = None):
    return problem_response(
        status=413,
        code=ErrorCode.PAYLOAD_TOO_LARGE,
        detail="Request exceeds allowed size.",
        correlation_id=correlation_id,
    )


def overload_reject_response(*, correlation_id: uuid.UUID | None = None):
    """Reject before acceptance when overload breakers trip."""
    return problem_response(
        status=503,
        code=ErrorCode.SERVICE_UNAVAILABLE,
        detail="Service is temporarily overloaded. Retry later.",
        correlation_id=correlation_id,
    )


class OverloadBreaker:
    """Simple in-process overload gate for tests and single-node dev."""

    def __init__(self, *, max_inflight: int = 256) -> None:
        self._max = max_inflight
        self._inflight = 0

    @property
    def inflight(self) -> int:
        return self._inflight

    def try_acquire(self) -> bool:
        if self._inflight >= self._max:
            return False
        self._inflight += 1
        return True

    def release(self) -> None:
        if self._inflight > 0:
            self._inflight -= 1


GLOBAL_OVERLOAD_BREAKER = OverloadBreaker()
