"""FastAPI application factory for Core."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from memdot_domain.types import HealthStatus

from memdot_core.errors import ErrorCode
from memdot_core.settings import CoreSettings


def create_app(settings: CoreSettings | None = None) -> FastAPI:
    resolved = settings or CoreSettings()
    resolved.validate_runtime()

    app = FastAPI(
        title="Memdot Core API",
        version="0.1.0",
        description="Canonical domain API skeleton. Product routes arrive in later phases.",
    )
    app.state.settings = resolved

    @app.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": HealthStatus.OK.value}

    @app.get("/health/ready", tags=["health"])
    def ready() -> dict[str, str]:
        return {"status": HealthStatus.OK.value, "service": "core"}

    @app.get("/api/v1/meta/error-codes", tags=["meta"])
    def error_codes() -> dict[str, list[str]]:
        return {"codes": [code.value for code in ErrorCode]}

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: object, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "code": ErrorCode.INTERNAL_ERROR.value,
            },
            media_type="application/problem+json",
        )

    return app
