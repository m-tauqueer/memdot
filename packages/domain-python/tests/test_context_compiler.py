"""Context compiler tests."""

from __future__ import annotations

import uuid

from memdot_domain.context_compiler import ContextBudget, compile_context
from memdot_domain.retrieval import CandidateLane, FusedCandidate


def test_compile_context_respects_budget() -> None:
    candidates = [
        FusedCandidate(
            candidate_id=f"c{i}",
            canonical_type="document",
            canonical_id=uuid.uuid4(),
            revision_id=uuid.uuid4(),
            space_id=uuid.uuid4(),
            fused_score=1.0,
            lanes=[CandidateLane.EXACT],
            snippet=f"snippet-{i}",
        )
        for i in range(5)
    ]
    corpus = {f"c{i}": "x" * 500 for i in range(5)}
    receipt = compile_context(
        query="snippet",
        purpose="first_party",
        policy_version="test-v1",
        eligible_spaces=[uuid.uuid4()],
        provider_versions={"local": "v1"},
        candidates=candidates,
        corpus_text=corpus,
        budget=ContextBudget(max_tokens=100, max_items=2),
    )
    selected = [item for item in receipt.items if item.selected]
    assert len(selected) <= 2
    assert receipt.partial is True
    assert receipt.context_hash
