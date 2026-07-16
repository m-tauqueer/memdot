"""Model-router policy: budgets, timeouts, and egress guards."""

from __future__ import annotations

from dataclasses import dataclass

from memdot_domain.ports.model import ModelBudget, StructuredCompletionRequest


@dataclass(frozen=True)
class RouterPolicy:
    default_budget: ModelBudget = ModelBudget()
    allowed_model_ids: frozenset[str] = frozenset({"local-echo-v1"})


def validate_request(request: StructuredCompletionRequest, policy: RouterPolicy) -> None:
    if request.budget.max_input_tokens > policy.default_budget.max_input_tokens:
        msg = "input_budget_exceeded"
        raise ValueError(msg)
    if request.budget.max_output_tokens > policy.default_budget.max_output_tokens:
        msg = "output_budget_exceeded"
        raise ValueError(msg)
    if request.budget.timeout_seconds > policy.default_budget.timeout_seconds:
        msg = "timeout_exceeded"
        raise ValueError(msg)


def select_model_id(request: StructuredCompletionRequest, policy: RouterPolicy) -> str:
    requested = str(request.payload.get("model_id") or "local-echo-v1")
    if requested not in policy.allowed_model_ids:
        msg = "model_not_allowed"
        raise ValueError(msg)
    return requested
