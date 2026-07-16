"""Temporal / as-of retrieval lane over historical document and memory revisions."""

from __future__ import annotations

import uuid
from datetime import datetime

from memdot_domain.retrieval import CandidateLane, RetrievalCandidate
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import DocumentRevision, MemoryRevision
from memdot_core.request_context import RequestContext


def temporal_candidates(
    db: Session,
    ctx: RequestContext,
    *,
    query: str,
    eligible_space_ids: set[uuid.UUID],
    as_of: datetime | None = None,
    max_results: int = 20,
) -> list[RetrievalCandidate]:
    """Return historical revisions matching query at or before as_of (when provided)."""
    trimmed = query.strip().lower()
    if not trimmed or not eligible_space_ids:
        return []

    results: list[RetrievalCandidate] = []
    doc_query = select(DocumentRevision).where(
        DocumentRevision.account_id == ctx.account_id,
        DocumentRevision.space_id.in_(eligible_space_ids),
        DocumentRevision.plain_text.is_not(None),
    )
    if as_of is not None:
        doc_query = doc_query.where(DocumentRevision.created_at <= as_of)

    for revision in db.execute(doc_query).scalars():
        text = (revision.plain_text or "").lower()
        if trimmed not in text:
            continue
        results.append(
            RetrievalCandidate(
                candidate_id=f"temporal:document:{revision.document_id}:{revision.id}",
                canonical_type="document",
                canonical_id=revision.document_id,
                revision_id=revision.id,
                space_id=revision.space_id,
                lane=CandidateLane.TEMPORAL_EXACT,
                rank=1,
                snippet=(revision.plain_text or "")[:512],
                score_hint=1.0,
            )
        )

    mem_query = select(MemoryRevision).where(
        MemoryRevision.account_id == ctx.account_id,
        MemoryRevision.space_id.in_(eligible_space_ids),
        MemoryRevision.status.in_(("active", "superseded")),
    )
    if as_of is not None:
        mem_query = mem_query.where(MemoryRevision.created_at <= as_of)

    for memory in db.execute(mem_query).scalars():
        if trimmed not in memory.assertion_text.lower():
            continue
        # Historical retrieval may surface superseded when as_of is set; otherwise active only.
        if as_of is None and memory.status != "active":
            continue
        results.append(
            RetrievalCandidate(
                candidate_id=f"temporal:memory:{memory.memory_item_id}:{memory.id}",
                canonical_type="memory",
                canonical_id=memory.memory_item_id,
                revision_id=memory.id,
                space_id=memory.space_id,
                lane=CandidateLane.TEMPORAL_EXACT,
                rank=1,
                snippet=memory.assertion_text[:512],
                score_hint=1.0,
            )
        )

    for index, candidate in enumerate(results[:max_results], start=1):
        results[index - 1] = RetrievalCandidate(
            candidate_id=candidate.candidate_id,
            canonical_type=candidate.canonical_type,
            canonical_id=candidate.canonical_id,
            revision_id=candidate.revision_id,
            space_id=candidate.space_id,
            lane=candidate.lane,
            rank=index,
            locator=candidate.locator,
            snippet=candidate.snippet,
            score_hint=candidate.score_hint,
        )
    return results[:max_results]
