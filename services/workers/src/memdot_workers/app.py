"""Minimal workers health application. No workflows in Phase 1."""

from fastapi import FastAPI
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
    def ready() -> dict[str, str]:
        return {"status": HealthStatus.OK.value, "service": "workers"}

    return app
