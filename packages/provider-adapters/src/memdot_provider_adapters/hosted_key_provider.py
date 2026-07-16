"""Hosted key-provider configuration seam (no cloud credentials)."""

from __future__ import annotations


class UnconfiguredHostedKeyProvider:
    """Phase 2 seam: hosted KMS wiring is declared but not credentialed."""

    def __init__(self, *, provider_name: str = "hosted-kms", configured: bool = False) -> None:
        self._provider_name = provider_name
        self._configured = configured

    def provider_name(self) -> str:
        return self._provider_name

    def is_configured(self) -> bool:
        return self._configured
