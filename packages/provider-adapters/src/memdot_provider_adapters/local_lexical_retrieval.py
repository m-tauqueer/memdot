"""In-memory exact substring retrieval over a supplied corpus."""

from __future__ import annotations

import uuid

from memdot_domain.ports.retrieval_provider import (
    RetrievalSearchRequest,
    RetrievalSearchResult,
)
from memdot_domain.retrieval import CandidateLane, RetrievalCandidate
from memdot_domain.types import HealthStatus


class LocalLexicalRetrievalAdapter:
    """Simple lexical candidate search for local rebuildable projections."""

    def __init__(self, corpus: dict[str, str]) -> None:
        self._corpus = corpus

    def health(self) -> HealthStatus:
        return HealthStatus.OK

    def search_candidates(self, request: RetrievalSearchRequest) -> RetrievalSearchResult:
        query = request.query.strip().lower()
        if not query:
            return RetrievalSearchResult(candidates=[], provider_version="local-lexical-v1")

        ranked: list[RetrievalCandidate] = []
        rank = 1
        for candidate_id, text in self._corpus.items():
            if query not in text.lower():
                continue
            parts = candidate_id.split(":", 2)
            canonical_type = parts[0] if parts else "unknown"
            canonical_id_raw = parts[1] if len(parts) > 1 else candidate_id
            revision_id_raw = parts[2] if len(parts) > 2 else canonical_id_raw

            ranked.append(
                RetrievalCandidate(
                    candidate_id=candidate_id,
                    canonical_type=canonical_type,
                    canonical_id=uuid.UUID(canonical_id_raw),
                    revision_id=uuid.UUID(revision_id_raw),
                    space_id=uuid.UUID(int=0),
                    lane=CandidateLane.EXACT,
                    rank=rank,
                    snippet=text[:512],
                )
            )
            rank += 1
            if len(ranked) >= request.limit:
                break

        return RetrievalSearchResult(
            candidates=ranked,
            provider_version="local-lexical-v1",
            circuit_open=False,
        )
