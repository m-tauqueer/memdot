"""Typed configuration for model-router."""

from memdot_domain.config_guards import (
    normalize_mode,
    reject_blank,
    reject_enabled_exporter_without_endpoint,
    reject_plaintext_provider_credential,
)
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelRouterSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODEL_ROUTER_", extra="ignore")

    host: str = "0.0.0.0"
    port: int = Field(default=8200, ge=1, le=65535)
    env: str = Field(default="development", min_length=1)
    log_level: str = Field(default="info", min_length=1)
    tex_enabled: bool = False
    telemetry_export: str = "off"
    otel_exporter_otlp_endpoint: str = ""
    provider_api_key: str = ""

    def validate_runtime(self) -> None:
        reject_blank("MODEL_ROUTER_ENV", self.env)
        mode = normalize_mode(self.env)
        if self.tex_enabled and mode in {"self_host", "development", "test"}:
            msg = "MODEL_ROUTER_TEX_ENABLED must remain false until Phase 7 provider wiring"
            raise ValueError(msg)
        reject_enabled_exporter_without_endpoint(
            export=self.telemetry_export,
            endpoint=self.otel_exporter_otlp_endpoint,
        )
        reject_plaintext_provider_credential(
            "MODEL_ROUTER_PROVIDER_API_KEY",
            self.provider_api_key or None,
            mode=mode,
        )
