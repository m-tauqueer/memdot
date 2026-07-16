"""Disabled Tex retrieval stub with circuit-open semantics."""

from __future__ import annotations

from memdot_domain.ports.retrieval_provider import (
    RetrievalSearchRequest,
    RetrievalSearchResult,
)
from memdot_domain.types import HealthStatus


class TexRetrievalStub:
    """Optional Tex provider; returns empty candidates when disabled."""

    def __init__(self, *, enabled: bool = False) -> None:
        self._enabled = enabled

    def health(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE if not self._enabled else HealthStatus.OK

    def search_candidates(self, request: RetrievalSearchRequest) -> RetrievalSearchResult:
        del request
        if not self._enabled:
            return RetrievalSearchResult(
                candidates=[],
                provider_version="tex-disabled-v1",
                circuit_open=True,
            )
        return RetrievalSearchResult(
            candidates=[],
            provider_version="tex-stub-v1",
            circuit_open=False,
        )

    def search_or_raise(self, request: RetrievalSearchRequest) -> RetrievalSearchResult:
        result = self.search_candidates(request)
        if result.circuit_open:
            msg = "tex_circuit_open"
            raise RuntimeError(msg)
        return result
