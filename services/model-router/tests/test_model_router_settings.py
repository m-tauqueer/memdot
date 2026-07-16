"""Model-router settings negative tests."""

import pytest
from memdot_model_router.settings import ModelRouterSettings


def test_rejects_tex_enabled_before_phase_7() -> None:
    settings = ModelRouterSettings(env="self_host", tex_enabled=True)
    with pytest.raises(ValueError, match="TEX_ENABLED"):
        settings.validate_runtime()


def test_rejects_exporter_without_endpoint() -> None:
    settings = ModelRouterSettings(
        env="development",
        telemetry_export="otlp",
        otel_exporter_otlp_endpoint="",
    )
    with pytest.raises(ValueError, match="exporter"):
        settings.validate_runtime()


def test_accepts_development_defaults() -> None:
    settings = ModelRouterSettings(env="development")
    settings.validate_runtime()
    assert settings.tex_enabled is False
