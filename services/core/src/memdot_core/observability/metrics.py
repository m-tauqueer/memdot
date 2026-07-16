"""In-process content-minimized metrics registry."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock

from memdot_domain.telemetry import sanitize_telemetry_attributes

_lock = Lock()
_counters: dict[str, int] = defaultdict(int)


def increment(counter_name: str, *, attributes: dict[str, object] | None = None) -> None:
    safe = sanitize_telemetry_attributes(attributes or {"counter_name": counter_name})
    key = f"{counter_name}:{safe.get('route', '')}:{safe.get('status_code', '')}"
    with _lock:
        _counters[key] += 1


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counters)


def reset() -> None:
    with _lock:
        _counters.clear()
