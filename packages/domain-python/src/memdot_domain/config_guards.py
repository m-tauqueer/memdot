"""Shared runtime-mode and secret-safety helpers for Memdot settings."""

from __future__ import annotations

from urllib.parse import urlparse

ALLOWED_MODES = frozenset({"hosted", "self_host", "test", "development"})
FORBIDDEN_SECRET_PLACEHOLDERS = frozenset(
    {
        "",
        "changeme",
        "password",
        "secret",
        "replace_with_operator_secret",
        "REPLACE_WITH_OPERATOR_SECRET",
    },
)


def normalize_mode(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        msg = "env must be a non-empty string"
        raise ValueError(msg)
    normalized = cleaned.lower().replace("-", "_")
    if normalized not in ALLOWED_MODES:
        msg = f"env must be one of {sorted(ALLOWED_MODES)}, got {value!r}"
        raise ValueError(msg)
    return normalized


def reject_blank(name: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        msg = f"{name} must be a non-empty string"
        raise ValueError(msg)
    return cleaned


def reject_production_placeholder(name: str, value: str, *, mode: str) -> None:
    if mode in {"development", "test"}:
        return
    if value.strip() in FORBIDDEN_SECRET_PLACEHOLDERS or value.strip().lower() in {
        item.lower() for item in FORBIDDEN_SECRET_PLACEHOLDERS
    }:
        msg = f"{name} rejects blank/default production secrets in mode={mode}"
        raise ValueError(msg)


def reject_unsafe_origin(name: str, origin: str) -> None:
    cleaned = origin.strip()
    if not cleaned:
        msg = f"{name} must be a non-empty origin"
        raise ValueError(msg)
    if "*" in cleaned:
        msg = f"{name} rejects wildcard trust"
        raise ValueError(msg)
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"}:
        msg = f"{name} must be an absolute http(s) origin"
        raise ValueError(msg)
    if not parsed.hostname:
        msg = f"{name} must include a hostname"
        raise ValueError(msg)
    if parsed.username is not None or parsed.password is not None:
        msg = f"{name} must not include credentials"
        raise ValueError(msg)
    if parsed.fragment:
        msg = f"{name} must not include a fragment"
        raise ValueError(msg)
    if parsed.path not in {"", "/"} or parsed.query:
        msg = f"{name} must be an origin (scheme://host[:port] only)"
        raise ValueError(msg)


def reject_malformed_url(name: str, url: str) -> None:
    cleaned = url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https", "postgresql", "postgres"}:
        msg = f"{name} must be an absolute URL"
        raise ValueError(msg)
    if not parsed.hostname:
        msg = f"{name} must include a hostname"
        raise ValueError(msg)
    if parsed.fragment:
        msg = f"{name} must not include a fragment"
        raise ValueError(msg)


def reject_enabled_exporter_without_endpoint(*, export: str, endpoint: str) -> None:
    if export.strip().lower() in {"", "off", "false", "0", "disabled"}:
        return
    if not endpoint.strip():
        msg = "telemetry exporter enabled without explicit endpoint"
        raise ValueError(msg)


def reject_plaintext_provider_credential(name: str, value: str | None, *, mode: str) -> None:
    if value is None or value.strip() == "":
        return
    # Reject plaintext provider credentials in production-like modes.
    if mode in {"hosted", "self_host"} and value.strip().startswith(
        ("sk-", "AIza", "ya29.", "ghp_", "xox"),
    ):
        msg = f"{name} must not embed plaintext provider credentials in config"
        raise ValueError(msg)
    if "BEGIN PRIVATE KEY" in value or "BEGIN RSA PRIVATE KEY" in value:
        msg = f"{name} must not embed plaintext private keys in config"
        raise ValueError(msg)
