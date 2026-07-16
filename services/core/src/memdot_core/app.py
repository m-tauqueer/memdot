"""FastAPI application factory for Core."""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from memdot_domain.health_probes import (
    probe_openbao_transit,
    probe_postgres_select1,
    probe_seaweed_s3,
)
from memdot_domain.types import HealthStatus

from memdot_core.errors import (
    ErrorCode,
    FieldError,
    correlation_id_from_request,
    problem_response,
    validation_problem,
)
from memdot_core.settings import CoreSettings


def create_app(settings: CoreSettings | None = None) -> FastAPI:
    resolved = settings or CoreSettings()
    resolved.validate_runtime()

    app = FastAPI(
        title="Memdot Core API",
        version="0.1.0",
        description="Canonical domain API. Adds documents, memory, context, sources, jobs, and ingestion routes.",
    )
    app.state.settings = resolved

    from memdot_core.auth.routes import router as auth_router
    from memdot_core.context.routes import router as context_router
    from memdot_core.documents.routes import router as documents_router
    from memdot_core.memory.routes import router as memory_router
    from memdot_core.sources.routes import router as sources_router  # noqa: PLC0415

    app.include_router(auth_router)
    app.include_router(sources_router)
    app.include_router(documents_router)
    app.include_router(memory_router)
    app.include_router(context_router)

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

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            FieldError(
                pointer="/" + "/".join(str(part) for part in err.get("loc", ()) if part != "body"),
                code=ErrorCode.VALIDATION_ERROR,
                detail=str(err.get("msg", "invalid")),
            )
            for err in exc.errors()
        ]
        return validation_problem(
            correlation_id=correlation_id_from_request(request),
            errors=errors,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: object, _exc: Exception) -> JSONResponse:
        return problem_response(
            status=500,
            code=ErrorCode.INTERNAL_ERROR,
            detail="An unexpected error occurred.",
        )

    return app
