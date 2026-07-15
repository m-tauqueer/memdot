"""Phase 1 stub memory-provider adapter (no network, no credentials)."""

from memdot_domain.types import HealthStatus


class StubMemoryProviderAdapter:
    """Implements MemoryProviderPort for boundary and wiring tests only."""

    def health(self) -> HealthStatus:
        return HealthStatus.OK
