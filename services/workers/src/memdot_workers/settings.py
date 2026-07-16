"""Typed configuration for workers."""

from memdot_domain.config_guards import (
    normalize_mode,
    reject_blank,
    reject_enabled_exporter_without_endpoint,
    reject_plaintext_provider_credential,
)
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkersSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKERS_", extra="ignore")

    health_host: str = "0.0.0.0"
    health_port: int = Field(default=8300, ge=1, le=65535)
    env: str = Field(default="development", min_length=1)
    log_level: str = Field(default="info", min_length=1)
    hatchet_host: str = "hatchet-engine"
    hatchet_port: int = Field(default=7070, ge=1, le=65535)
    telemetry_export: str = "off"
    otel_exporter_otlp_endpoint: str = ""
    provider_api_key: str = ""

    def validate_runtime(self) -> None:
        reject_blank("WORKERS_ENV", self.env)
        mode = normalize_mode(self.env)
        reject_blank("WORKERS_HATCHET_HOST", self.hatchet_host)
        reject_enabled_exporter_without_endpoint(
            export=self.telemetry_export,
            endpoint=self.otel_exporter_otlp_endpoint,
        )
        reject_plaintext_provider_credential(
            "WORKERS_PROVIDER_API_KEY",
            self.provider_api_key or None,
            mode=mode,
        )
