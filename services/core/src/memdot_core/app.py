"""FastAPI application factory for Core."""

from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from memdot_domain.health_probes import (
    probe_openbao_transit,
    probe_postgres_select1,
    probe_seaweed_s3,
)
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
    def ready(response: Response) -> dict[str, str]:
        # Liveness stays up; readiness reflects required infra when configured.
        # Telemetry/OTel is optional and never gates readiness.
        pg = probe_postgres_select1(resolved.database_url)
        if resolved.database_url.strip() and not pg.ok:
            response.status_code = 503
            return {"status": "degraded", "service": "core", "dependency": "postgres"}

        token = resolved.resolve_transit_token()
        bao = probe_openbao_transit(resolved.openbao_addr, token)
        if resolved.openbao_addr.strip() and not bao.ok:
            response.status_code = 503
            return {"status": "degraded", "service": "core", "dependency": "openbao"}

        s3 = probe_seaweed_s3(
            resolved.object_store_endpoint,
            resolved.object_store_access_key,
            resolved.object_store_secret_key,
        )
        if resolved.object_store_endpoint.strip() and not s3.ok:
            response.status_code = 503
            return {"status": "degraded", "service": "core", "dependency": "seaweedfs"}

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
