"""Hosted key-provider seam — no cloud credentials in Phase 2."""

from typing import Protocol


class HostedKeyProviderPort(Protocol):
    """Configuration seam for hosted KMS-style providers (implemented later)."""

    def provider_name(self) -> str:
        """Return the provider identifier without contacting cloud APIs."""
        ...

    def is_configured(self) -> bool:
        """Return True only when required hosted configuration is present."""
        ...
