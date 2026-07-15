"""Memdot domain package — types and provider ports only in Phase 1."""

from memdot_domain.ports.memory_provider import MemoryProviderPort
from memdot_domain.types import HealthStatus

__all__ = ["HealthStatus", "MemoryProviderPort"]
