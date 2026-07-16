"""Model-router policy tests."""

from __future__ import annotations

import pytest
from memdot_domain.ports.model import ModelBudget, StructuredCompletionRequest
from memdot_model_router.adapters import DEFAULT_ADAPTER, DEFAULT_POLICY
from memdot_model_router.policy import validate_request


def test_validate_request_rejects_excessive_timeout() -> None:
    request = StructuredCompletionRequest(
        schema_name="echo",
        payload={"model_id": "local-echo-v1"},
        budget=ModelBudget(timeout_seconds=999.0),
    )
    with pytest.raises(ValueError, match="timeout_exceeded"):
        validate_request(request, DEFAULT_POLICY)


def test_local_echo_adapter_returns_structured_output() -> None:
    request = StructuredCompletionRequest(
        schema_name="echo",
        payload={"model_id": "local-echo-v1", "message": "hi"},
        budget=ModelBudget(),
    )
    result = DEFAULT_ADAPTER.complete_structured(request, policy=DEFAULT_POLICY)
    assert result.output["schema"] == "echo"
    assert result.model_id == "local-echo-v1"
