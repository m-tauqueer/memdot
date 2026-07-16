"""Local model adapter stubs behind the router boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass

from memdot_domain.ports.model import (
    ModelBudget,
    StructuredCompletionRequest,
    StructuredCompletionResult,
)
from memdot_domain.types import HealthStatus

from memdot_model_router.policy import RouterPolicy, select_model_id, validate_request


@dataclass(frozen=True)
class LocalEchoAdapter:
    model_id: str = "local-echo-v1"

    def health(self) -> HealthStatus:
        return HealthStatus.OK

    def complete_structured(
        self, request: StructuredCompletionRequest, *, policy: RouterPolicy
    ) -> StructuredCompletionResult:
        validate_request(request, policy)
        model_id = select_model_id(request, policy)
        canonical = json.dumps(request.payload, sort_keys=True, separators=(",", ":"))
        return StructuredCompletionResult(
            output={"echo": request.payload, "schema": request.schema_name},
            model_id=model_id,
            input_tokens=max(1, len(canonical) // 4),
            output_tokens=min(request.budget.max_output_tokens, 64),
        )


DEFAULT_POLICY = RouterPolicy()
DEFAULT_ADAPTER = LocalEchoAdapter()
