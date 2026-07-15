"""Memory provider port definition."""

from typing import Protocol

from memdot_domain.types import HealthStatus


class MemoryProviderPort(Protocol):
    """Retrieval provider port. Implementations must not own authorization."""

    def health(self) -> HealthStatus:
        """Return provider health without inspecting user content."""
        ...
