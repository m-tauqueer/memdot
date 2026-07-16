"""Retrieval candidate lanes, RRF fusion, and private-space exclusion."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeVar

from memdot_domain.tenancy import SpaceVisibility


class CandidateLane(StrEnum):
    TEMPORAL_EXACT = "temporal_exact"
    EXACT = "exact"
    OSS_SEMANTIC = "oss_semantic"
    TEX = "tex"
    GRAPH = "graph"


# TRD-RET-004 initial weights (k=60).
RRF_K = 60
LANE_WEIGHTS: dict[CandidateLane, float] = {
    CandidateLane.TEMPORAL_EXACT: 2.0,
    CandidateLane.EXACT: 1.5,
    CandidateLane.OSS_SEMANTIC: 1.0,
    CandidateLane.TEX: 1.0,
    CandidateLane.GRAPH: 0.8,
}


@dataclass(frozen=True)
class RetrievalCandidate:
    candidate_id: str
    canonical_type: str
    canonical_id: uuid.UUID
    revision_id: uuid.UUID
    space_id: uuid.UUID
    lane: CandidateLane
    rank: int
    locator: str | None = None
    snippet: str | None = None
    score_hint: float | None = None


@dataclass
class FusedCandidate:
    candidate_id: str
    canonical_type: str
    canonical_id: uuid.UUID
    revision_id: uuid.UUID
    space_id: uuid.UUID
    fused_score: float
    lanes: list[CandidateLane] = field(default_factory=lambda: [])
    locator: str | None = None
    snippet: str | None = None


_CandidateT = TypeVar("_CandidateT", FusedCandidate, RetrievalCandidate)


def rrf_contribution(rank: int, *, weight: float, k: int = RRF_K) -> float:
    return weight / (k + rank)


def fuse_candidates(
    lane_results: dict[CandidateLane, list[RetrievalCandidate]],
    *,
    k: int = RRF_K,
    weights: dict[CandidateLane, float] | None = None,
) -> list[FusedCandidate]:
    """Deterministic weighted reciprocal-rank fusion."""
    active_weights = weights or LANE_WEIGHTS
    scores: dict[str, FusedCandidate] = {}
    for lane, candidates in lane_results.items():
        weight = active_weights.get(lane, 1.0)
        for candidate in candidates:
            key = candidate.candidate_id
            contrib = rrf_contribution(candidate.rank, weight=weight, k=k)
            if key not in scores:
                scores[key] = FusedCandidate(
                    candidate_id=key,
                    canonical_type=candidate.canonical_type,
                    canonical_id=candidate.canonical_id,
                    revision_id=candidate.revision_id,
                    space_id=candidate.space_id,
                    fused_score=contrib,
                    lanes=[lane],
                    locator=candidate.locator,
                    snippet=candidate.snippet,
                )
            else:
                existing = scores[key]
                existing.fused_score += contrib
                existing.lanes.append(lane)
                if existing.locator is None and candidate.locator:
                    existing.locator = candidate.locator
                if existing.snippet is None and candidate.snippet:
                    existing.snippet = candidate.snippet
    ordered = sorted(
        scores.values(),
        key=lambda item: (-item.fused_score, item.candidate_id),
    )
    return ordered


def exclude_private_spaces(
    candidates: Sequence[_CandidateT],
    *,
    space_visibility: dict[uuid.UUID, SpaceVisibility],
    purpose: str,
) -> list[_CandidateT]:
    """Drop private-space candidates for external read purposes."""
    if purpose != "external_read":
        return list(candidates)
    filtered: list[_CandidateT] = []
    for candidate in candidates:
        visibility = space_visibility.get(candidate.space_id, SpaceVisibility.GENERAL)
        if visibility == SpaceVisibility.PRIVATE:
            continue
        filtered.append(candidate)
    return filtered
