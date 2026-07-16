"""Overload breaker policy tests."""

from __future__ import annotations

from memdot_core.policy import OverloadBreaker, overload_reject_response


def test_overload_breaker_rejects_when_full() -> None:
    breaker = OverloadBreaker(max_inflight=1)
    assert breaker.try_acquire() is True
    assert breaker.try_acquire() is False
    breaker.release()
    assert breaker.try_acquire() is True


def test_overload_response_is_safe() -> None:
    response = overload_reject_response()
    assert response.status_code == 503
