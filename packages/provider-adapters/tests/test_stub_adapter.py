from memdot_domain.types import HealthStatus
from memdot_provider_adapters import StubMemoryProviderAdapter


def test_stub_adapter_health() -> None:
    assert StubMemoryProviderAdapter().health() is HealthStatus.OK
