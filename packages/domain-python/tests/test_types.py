from memdot_domain.types import ComponentHealth, HealthStatus


def test_component_health_defaults() -> None:
    health = ComponentHealth(component="domain")
    assert health.status is HealthStatus.OK
    assert health.component == "domain"
