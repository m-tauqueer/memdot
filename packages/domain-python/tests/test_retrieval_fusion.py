"""Retrieval fusion tests."""

from __future__ import annotations

import uuid

from memdot_domain.retrieval import (
    LANE_WEIGHTS,
    RRF_K,
    CandidateLane,
    RetrievalCandidate,
    fuse_candidates,
    rrf_contribution,
)


def _candidate(
    candidate_id: str, lane: CandidateLane, rank: int, *, space_id: uuid.UUID | None = None
) -> RetrievalCandidate:
    sid = space_id or uuid.uuid4()
    canonical = uuid.uuid4()
    return RetrievalCandidate(
        candidate_id=candidate_id,
        canonical_type="document",
        canonical_id=canonical,
        revision_id=uuid.uuid4(),
        space_id=sid,
        lane=lane,
        rank=rank,
    )


def test_rrf_contribution_uses_k60_and_weight() -> None:
    weight = LANE_WEIGHTS[CandidateLane.EXACT]
    assert rrf_contribution(1, weight=weight, k=RRF_K) == weight / (RRF_K + 1)


def test_fuse_candidates_is_deterministic() -> None:
    lane_results = {
        CandidateLane.EXACT: [_candidate("a", CandidateLane.EXACT, 1)],
        CandidateLane.TEX: [
            _candidate("a", CandidateLane.TEX, 2),
            _candidate("b", CandidateLane.TEX, 1),
        ],
    }
    fused = fuse_candidates(lane_results)
    assert fused[0].candidate_id == "a"
    assert CandidateLane.EXACT in fused[0].lanes
    assert fused[1].candidate_id == "b"
