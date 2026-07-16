"""Telemetry allowlist tests."""

from __future__ import annotations

import pytest
from memdot_domain.telemetry import (
    TelemetryContentRejectedError,
    reject_forbidden_telemetry_fields,
    sanitize_telemetry_attributes,
)


def test_rejects_user_content_fields() -> None:
    with pytest.raises(TelemetryContentRejectedError):
        reject_forbidden_telemetry_fields({"query": "secret question"})


def test_allows_safe_metadata() -> None:
    payload = sanitize_telemetry_attributes(
        {"route": "/api/v1/mcp/search", "status_code": 200, "duration_ms": 12}
    )
    assert payload["route"] == "/api/v1/mcp/search"
    assert payload["status_code"] == 200


def test_nested_forbidden_field_rejected() -> None:
    with pytest.raises(TelemetryContentRejectedError):
        reject_forbidden_telemetry_fields({"meta": {"content": "user wrote this"}})
