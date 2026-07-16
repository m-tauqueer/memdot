"""Config guard and redaction unit tests."""

import pytest
from memdot_domain.config_guards import (
    normalize_mode,
    reject_enabled_exporter_without_endpoint,
    reject_production_placeholder,
    reject_unsafe_origin,
)
from memdot_domain.redaction import assert_no_forbidden_content, redact_secrets


def test_normalize_mode_accepts_supported_values() -> None:
    assert normalize_mode("self_host") == "self_host"
    assert normalize_mode("Development") == "development"


def test_normalize_mode_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="env must be one of"):
        normalize_mode("staging")


def test_reject_origin_with_credentials() -> None:
    with pytest.raises(ValueError, match="credentials"):
        reject_unsafe_origin("ORIGIN", "https://user:pass@example.com")


def test_reject_origin_with_path() -> None:
    with pytest.raises(ValueError, match="origin"):
        reject_unsafe_origin("ORIGIN", "https://example.com/app")


def test_reject_exporter_without_endpoint() -> None:
    with pytest.raises(ValueError, match="exporter"):
        reject_enabled_exporter_without_endpoint(export="otlp", endpoint="")


def test_reject_production_placeholder() -> None:
    with pytest.raises(ValueError, match="production secrets"):
        reject_production_placeholder(
            "TOKEN",
            "REPLACE_WITH_OPERATOR_SECRET",
            mode="self_host",
        )


def test_redact_secrets_masks_password_and_dsn() -> None:
    text = "password=supersecret postgres://memdot:hunter2@postgres:5432/memdot"
    redacted = redact_secrets(text)
    assert "supersecret" not in redacted
    assert "hunter2" not in redacted
    assert "[REDACTED]" in redacted


def test_forbidden_content_denylist() -> None:
    with pytest.raises(ValueError, match="forbidden content"):
        assert_no_forbidden_content("user submitted prompt: hello")
