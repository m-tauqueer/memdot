"""Telemetry field allowlist — user content must never leave services."""

from __future__ import annotations

from typing import Any, cast

# Content-bearing keys rejected from telemetry/log/metric attribute sinks.
FORBIDDEN_TELEMETRY_KEYS: frozenset[str] = frozenset(
    {
        "content",
        "text",
        "body",
        "prompt",
        "completion",
        "message",
        "user_content",
        "assertion_text",
        "plain_text",
        "exact_text",
        "sealed_answer",
        "patch_json",
        "payload",
        "conversation_turn",
        "turn_content",
        "query",
        "snippet",
        "corpus",
        "document_json",
        "memdot_document",
        "raw_turn",
        "captured_text",
    }
)

# Safe metadata keys permitted in observability sinks.
ALLOWED_TELEMETRY_KEYS: frozenset[str] = frozenset(
    {
        "account_id",
        "actor_id",
        "correlation_id",
        "request_id",
        "service",
        "route",
        "method",
        "status_code",
        "error_code",
        "duration_ms",
        "job_type",
        "job_id",
        "event_type",
        "entity_type",
        "entity_id",
        "space_id",
        "purpose",
        "scope",
        "client_id",
        "tool_name",
        "counter_name",
        "count",
        "dependency",
        "degraded",
        "partial",
    }
)


class TelemetryContentRejectedError(ValueError):
    """Raised when telemetry payload contains forbidden user-content fields."""


from typing import Any, cast


def _walk_keys(value: object, *, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        mapping = cast(dict[object, object], value)
        for key, nested in mapping.items():
            key_str = str(key)
            path = f"{prefix}.{key_str}" if prefix else key_str
            keys.append(path)
            keys.extend(_walk_keys(nested, prefix=path))
    elif isinstance(value, list):
        items = cast(list[object], value)
        for index, nested in enumerate(items):
            path = f"{prefix}[{index}]"
            keys.extend(_walk_keys(nested, prefix=path))
    return keys


def reject_forbidden_telemetry_fields(payload: dict[str, Any]) -> None:
    """Fail closed when payload keys match the user-content denylist."""
    for path in _walk_keys(payload):
        leaf = path.split(".")[-1].split("[")[0].lower()
        if leaf in FORBIDDEN_TELEMETRY_KEYS:
            msg = f"forbidden telemetry field: {path}"
            raise TelemetryContentRejectedError(msg)


def sanitize_telemetry_attributes(
    payload: dict[str, Any],
    *,
    extra_allowed: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Return only allowlisted scalar attributes for metrics/logs."""
    reject_forbidden_telemetry_fields(payload)
    allowed = ALLOWED_TELEMETRY_KEYS | (extra_allowed or frozenset())
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in allowed:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key] = value
    return sanitized
