"""Pure canary assertion helpers (no Hatchet SDK import at module load)."""

from __future__ import annotations

import asyncio
from typing import Any


class CanaryTimeoutError(TimeoutError):
    """Outer/canary wait exceeded MEMDOT_CANARY_TIMEOUT_SEC."""


class UnexpectedCanaryFailure(RuntimeError):
    """Transport/cancellation/unexpected exception — not proof of controlled failure."""


def sync_result_with_timeout(ref: Any, timeout_sec: float) -> dict[str, Any]:
    """Await workflow result with a real wall-clock timeout on one event loop.

    Must not use a ThreadPoolExecutor around sync_result — Hatchet's gRPC
    listener is loop-bound and cross-loop waits raise StopAsyncIteration.
    """

    async def _wait() -> dict[str, Any]:
        return await asyncio.wait_for(ref.result(), timeout=timeout_sec)

    def _no_loop() -> asyncio.AbstractEventLoop | None:
        return None

    try:
        from hatchet_sdk.utils.aio_utils import get_active_event_loop as _get_loop
    except Exception:  # noqa: BLE001
        _get_loop = _no_loop

    loop = _get_loop()
    owns_loop = False
    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        owns_loop = True
    try:
        return loop.run_until_complete(_wait())
    except TimeoutError as exc:
        # asyncio.TimeoutError is an alias of TimeoutError on 3.12+
        raise CanaryTimeoutError(f"sync_result exceeded timeout_sec={timeout_sec}") from exc
    finally:
        if owns_loop:
            asyncio.set_event_loop(None)
            loop.close()


def is_expected_terminal_failure(exc: BaseException) -> bool:
    """Accept only Hatchet workflow-error terminals for the controlled-fail path."""
    if isinstance(exc, CanaryTimeoutError):
        return False
    if type(exc).__name__ == "DedupeViolationErr":
        return False
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return False
    if type(exc).__name__ == "StopAsyncIteration":
        return False
    text = str(exc)
    if "Workflow Errors:" not in text:
        return False
    return "intentional canary failure" in text
