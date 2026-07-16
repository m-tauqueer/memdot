"""Retrieval provider port for candidate search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from memdot_domain.retrieval import CandidateLane, RetrievalCandidate
from memdot_domain.types import HealthStatus


@dataclass(frozen=True)
class RetrievalSearchRequest:
    query: str
    lanes: frozenset[CandidateLane]
    limit: int = 50


@dataclass(frozen=True)
class RetrievalSearchResult:
    candidates: list[RetrievalCandidate]
    provider_version: str
    circuit_open: bool = False


class RetrievalProviderPort(Protocol):
    """Optional Tex or local retrieval; must not own authorization."""

    def health(self) -> HealthStatus:
        """Return provider health without inspecting user content."""
        ...

    def search_candidates(self, request: RetrievalSearchRequest) -> RetrievalSearchResult:
        """Return ranked candidates for fusion; Tex is optional."""
        ...
