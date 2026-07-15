"""Model-router health application. No providers in Phase 1."""

from fastapi import FastAPI
from memdot_domain.types import HealthStatus

from memdot_model_router.settings import ModelRouterSettings


def create_app(settings: ModelRouterSettings | None = None) -> FastAPI:
    resolved = settings or ModelRouterSettings()
    resolved.validate_runtime()
    app = FastAPI(title="Memdot Model Router", version="0.1.0")
    app.state.settings = resolved

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": HealthStatus.OK.value}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        return {"status": HealthStatus.OK.value, "service": "model-router"}

    return app
