"""Model provider port for structured completion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from memdot_domain.types import HealthStatus


@dataclass(frozen=True)
class ModelBudget:
    max_input_tokens: int = 8192
    max_output_tokens: int = 1024
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class StructuredCompletionRequest:
    schema_name: str
    payload: dict[str, Any]
    budget: ModelBudget


@dataclass(frozen=True)
class StructuredCompletionResult:
    output: dict[str, Any]
    model_id: str
    input_tokens: int
    output_tokens: int


class ModelPort(Protocol):
    """Isolated model egress port; implementations must not own authorization."""

    def health(self) -> HealthStatus:
        """Return provider health without inspecting user content."""
        ...

    def complete_structured(
        self, request: StructuredCompletionRequest
    ) -> StructuredCompletionResult:
        """Return schema-constrained output within budget and timeout."""
        ...
