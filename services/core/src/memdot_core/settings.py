"""Typed configuration for Core."""

from pathlib import Path

from memdot_domain.config_guards import (
    normalize_mode,
    reject_blank,
    reject_enabled_exporter_without_endpoint,
    reject_malformed_url,
    reject_plaintext_provider_credential,
    reject_production_placeholder,
    reject_unsafe_origin,
)
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CORE_", extra="ignore")

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    env: str = Field(default="development", min_length=1)
    log_level: str = Field(default="info", min_length=1)
    database_url: str = ""
    object_store_endpoint: str = ""
    object_store_access_key: str = ""
    object_store_secret_key: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = "memdot-core"
    openbao_addr: str = ""
    openbao_transit_token: str = ""
    openbao_transit_token_file: str = "/run/secrets/openbao_transit_token"
    allowed_origins: str = "http://localhost:3000"
    telemetry_export: str = "off"
    otel_exporter_otlp_endpoint: str = ""
    provider_api_key: str = ""
    session_signing_pepper: str = Field(default="dev-session-pepper-change-me", min_length=16)
    tenant_context_signing_key: str = Field(
        default="dev-tenant-context-signing-key-change-me", min_length=32
    )
    oidc_client_id: str = "memdot-core"
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = "http://localhost:8000/api/v1/auth/oidc/callback"

    def is_hosted(self) -> bool:
        return normalize_mode(self.env) == "hosted"

    def is_self_host(self) -> bool:
        return normalize_mode(self.env) == "self_host"

    def resolve_transit_token(self) -> str:
        if self.openbao_transit_token.strip():
            return self.openbao_transit_token.strip()
        path = Path(self.openbao_transit_token_file)
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
        return ""

    def validate_runtime(self) -> None:
        reject_blank("CORE_ENV", self.env)
        mode = normalize_mode(self.env)
        reject_blank("CORE_OIDC_AUDIENCE", self.oidc_audience)
        reject_blank("CORE_OIDC_CLIENT_ID", self.oidc_client_id)
        for origin in self.allowed_origins.split(","):
            reject_unsafe_origin("CORE_ALLOWED_ORIGINS", origin)
        reject_enabled_exporter_without_endpoint(
            export=self.telemetry_export,
            endpoint=self.otel_exporter_otlp_endpoint,
        )
        reject_plaintext_provider_credential(
            "CORE_PROVIDER_API_KEY",
            self.provider_api_key or None,
            mode=mode,
        )
        if mode in {"self_host", "hosted"}:
            reject_malformed_url("CORE_DATABASE_URL", self.database_url)
            reject_malformed_url("CORE_OBJECT_STORE_ENDPOINT", self.object_store_endpoint)
            reject_malformed_url("CORE_OIDC_ISSUER", self.oidc_issuer)
            reject_malformed_url("CORE_OIDC_REDIRECT_URI", self.oidc_redirect_uri)
            reject_production_placeholder(
                "CORE_TENANT_CONTEXT_SIGNING_KEY",
                self.tenant_context_signing_key,
                mode=mode,
            )
            reject_production_placeholder(
                "CORE_SESSION_SIGNING_PEPPER",
                self.session_signing_pepper,
                mode=mode,
            )
            if not self.oidc_audience.strip():
                msg = "CORE_OIDC_AUDIENCE must be set when CORE_OIDC_ISSUER is configured"
                raise ValueError(msg)
            if mode == "self_host":
                reject_malformed_url("CORE_OPENBAO_ADDR", self.openbao_addr)
                token = self.resolve_transit_token()
                reject_production_placeholder(
                    "CORE_OPENBAO_TRANSIT_TOKEN",
                    token,
                    mode=mode,
                )
                if token.strip().lower() in {"root", "dev-root-token"}:
                    msg = "CORE_OPENBAO_TRANSIT_TOKEN must not be a root/bootstrap token"
                    raise ValueError(msg)
