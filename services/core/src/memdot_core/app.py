"""FastAPI application factory for Core."""

from __future__ import annotations

import logging
import os

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


def _sync_runtime_secrets(settings: CoreSettings) -> None:
    os.environ.setdefault("CORE_SESSION_SIGNING_PEPPER", settings.session_signing_pepper)
    os.environ.setdefault("CORE_TENANT_CONTEXT_SIGNING_KEY", settings.tenant_context_signing_key)
    os.environ.setdefault("CORE_MCP_SERVICE_SECRET", settings.mcp_service_secret)
    if settings.job_auth_snapshot_key:
        os.environ.setdefault("CORE_JOB_AUTH_SNAPSHOT_KEY", settings.job_auth_snapshot_key)
    if settings.mcp_jwt_hs256_key:
        os.environ.setdefault("CORE_MCP_JWT_HS256_KEY", settings.mcp_jwt_hs256_key)
    if settings.oidc_issuer:
        os.environ.setdefault("CORE_OIDC_ISSUER", settings.oidc_issuer)
    if settings.oidc_audience:
        os.environ.setdefault("CORE_OIDC_AUDIENCE", settings.oidc_audience)
    if settings.mcp_resource:
        os.environ.setdefault("CORE_MCP_RESOURCE", settings.mcp_resource)


class TelemetryRedactingFilter(logging.Filter):
    """Sanitize log records that include forbidden content keys."""

    _BASE_KEYS = frozenset(logging.makeLogRecord({}).__dict__.keys())

    def filter(self, record: logging.LogRecord) -> bool:
        from memdot_domain.telemetry import FORBIDDEN_TELEMETRY_KEYS

        for key in list(record.__dict__):
            if key in self._BASE_KEYS or key.startswith("_"):
                continue
            if key.lower() in FORBIDDEN_TELEMETRY_KEYS:
                setattr(record, key, "[redacted]")
        try:
            message = str(record.getMessage())
        except Exception:
            return True
        lowered = message.lower()
        if any(
            f"{forbidden}=" in lowered or f'"{forbidden}"' in lowered
            for forbidden in FORBIDDEN_TELEMETRY_KEYS
        ):
            record.msg = "[redacted-log]"
            record.args = ()
        return True


def create_app(settings: CoreSettings | None = None) -> FastAPI:
    resolved = settings or CoreSettings()
    resolved.validate_runtime()
    _sync_runtime_secrets(resolved)

    app = FastAPI(
        title="Memdot Core API",
        version="0.1.0",
        description=(
            "Canonical domain API. Adds documents, memory, context, sources, "
            "jobs, and ingestion routes."
        ),
    )
    app.state.settings = resolved
    logging.getLogger("memdot_core").addFilter(TelemetryRedactingFilter())

    from memdot_core.auth.routes import router as auth_router
    from memdot_core.context.routes import router as context_router
    from memdot_core.conversations.routes import router as conversations_router
    from memdot_core.deletion.routes import router as deletion_router
    from memdot_core.documents.routes import router as documents_router
    from memdot_core.export.routes import router as export_router
    from memdot_core.learning.routes import router as learning_router
    from memdot_core.mcp.routes import router as mcp_router
    from memdot_core.memory.routes import router as memory_router
    from memdot_core.notion.routes import router as notion_router
    from memdot_core.sources.routes import router as sources_router  # noqa: PLC0415

    app.include_router(auth_router)
    app.include_router(sources_router)
    app.include_router(documents_router)
    app.include_router(memory_router)
    app.include_router(context_router)
    app.include_router(learning_router)
    app.include_router(mcp_router)
    app.include_router(conversations_router)
    app.include_router(notion_router)
    app.include_router(export_router)
    app.include_router(deletion_router)

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

    @app.get("/api/v1/metrics", tags=["observability"])
    def metrics() -> dict[str, object]:
        from memdot_core.observability.metrics import snapshot

        return {"counters": snapshot()}

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
