"""Typed configuration for Core."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CORE_", extra="ignore")

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    env: str = Field(default="development", min_length=1)
    log_level: str = Field(default="info", min_length=1)

    def validate_runtime(self) -> None:
        if not self.env.strip():
            msg = "CORE_ENV must be a non-empty string"
            raise ValueError(msg)
