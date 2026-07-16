"""Workers settings negative tests."""

import pytest
from memdot_workers.settings import WorkersSettings


def test_rejects_unknown_mode() -> None:
    settings = WorkersSettings(env="staging")
    with pytest.raises(ValueError, match="env must be one of"):
        settings.validate_runtime()


def test_rejects_exporter_without_endpoint() -> None:
    settings = WorkersSettings(
        env="development", telemetry_export="otlp", otel_exporter_otlp_endpoint=""
    )
    with pytest.raises(ValueError, match="exporter"):
        settings.validate_runtime()


def test_rejects_plaintext_provider_key_in_hosted() -> None:
    settings = WorkersSettings(env="hosted", provider_api_key="sk-live-example")
    with pytest.raises(ValueError, match="plaintext provider"):
        settings.validate_runtime()
