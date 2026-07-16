"""Secret redaction helpers for logs, health, and telemetry sinks."""

from __future__ import annotations

import re

_REDACTED = "[REDACTED]"

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)(\S+)"),
    re.compile(r"(postgres(?:ql)?://[^:\s]+):([^@\s]+)@"),
    re.compile(r"(?i)(x-vault-token:\s*)(\S+)"),
)


def redact_secrets(text: str) -> str:
    """Return text with credential-like values replaced. Content-free safe."""
    redacted = text
    for pattern in _PATTERNS:
        if pattern.groups >= 2 and "postgres" in pattern.pattern:
            redacted = pattern.sub(rf"\1:{_REDACTED}@", redacted)
        elif pattern.groups >= 2:
            redacted = pattern.sub(rf"\1{_REDACTED}", redacted)
        else:
            redacted = pattern.sub(_REDACTED, redacted)
    return redacted


def assert_no_forbidden_content(text: str, *, denylist: list[str] | None = None) -> None:
    """Raise ValueError when denylisted content appears in telemetry/log sinks."""
    blocked = denylist or [
        "BEGIN PRIVATE KEY",
        "cookie=",
        "set-cookie:",
        "prompt:",
        "user content",
    ]
    lowered = text.lower()
    for item in blocked:
        if item.lower() in lowered:
            msg = "forbidden content present in telemetry/log sink"
            raise ValueError(msg)
