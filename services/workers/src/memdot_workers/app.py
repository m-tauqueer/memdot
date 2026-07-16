"""Minimal workers health application. Workflows arrive via Hatchet workers."""

from fastapi import FastAPI, Response
from memdot_domain.health_probes import probe_tcp_host_port
from memdot_domain.types import HealthStatus

from memdot_workers.settings import WorkersSettings


def create_app(settings: WorkersSettings | None = None) -> FastAPI:
    resolved = settings or WorkersSettings()
    resolved.validate_runtime()
    app = FastAPI(title="Memdot Workers", version="0.1.0")
    app.state.settings = resolved

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": HealthStatus.OK.value}

    @app.get("/health/ready")
    def ready(response: Response) -> dict[str, str]:
        # Readiness degrades when Hatchet engine is unreachable.
        # Telemetry outage must not fail readiness.
        probe = probe_tcp_host_port(resolved.hatchet_host, resolved.hatchet_port)
        if not probe.ok:
            response.status_code = 503
            return {"status": "degraded", "service": "workers", "dependency": "hatchet"}
        return {"status": HealthStatus.OK.value, "service": "workers"}

    return app
