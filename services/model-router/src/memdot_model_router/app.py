"""Model-router HTTP application."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from memdot_domain.ports.model import ModelBudget, StructuredCompletionRequest
from memdot_domain.types import HealthStatus
from pydantic import BaseModel, Field

from memdot_model_router.adapters import DEFAULT_ADAPTER, DEFAULT_POLICY
from memdot_model_router.settings import ModelRouterSettings


class CompleteBody(BaseModel):
    schema_name: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    max_input_tokens: int = Field(default=8192, ge=256, le=65536)
    max_output_tokens: int = Field(default=1024, ge=64, le=8192)
    timeout_seconds: float = Field(default=30.0, ge=0.1, le=120.0)


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

    @app.post("/v1/complete")
    def complete(body: CompleteBody) -> dict[str, Any]:
        request = StructuredCompletionRequest(
            schema_name=body.schema_name,
            payload=body.payload,
            budget=ModelBudget(
                max_input_tokens=body.max_input_tokens,
                max_output_tokens=body.max_output_tokens,
                timeout_seconds=body.timeout_seconds,
            ),
        )
        try:
            result = DEFAULT_ADAPTER.complete_structured(request, policy=DEFAULT_POLICY)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "output": result.output,
            "modelId": result.model_id,
            "inputTokens": result.input_tokens,
            "outputTokens": result.output_tokens,
        }

    return app
