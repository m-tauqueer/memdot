"""Graph retrieval lane over confirmed/suggested curriculum and memory relations."""

from __future__ import annotations

import uuid

from memdot_domain.retrieval import CandidateLane, RetrievalCandidate
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import CurriculumEdge, CurriculumNode, MemoryRevision
from memdot_core.request_context import RequestContext


def graph_candidates(
    db: Session,
    ctx: RequestContext,
    *,
    query: str,
    eligible_space_ids: set[uuid.UUID],
    max_results: int = 20,
) -> list[RetrievalCandidate]:
    trimmed = query.strip().lower()
    if not trimmed or not eligible_space_ids:
        return []

    nodes = (
        db.execute(
            select(CurriculumNode).where(
                CurriculumNode.account_id == ctx.account_id,
                CurriculumNode.space_id.in_(eligible_space_ids),
            )
        )
        .scalars()
        .all()
    )
    matching_nodes = [node for node in nodes if trimmed in node.title.lower()]
    if not matching_nodes:
        return []

    node_ids = {node.id for node in matching_nodes}
    edges = (
        db.execute(
            select(CurriculumEdge).where(
                CurriculumEdge.account_id == ctx.account_id,
                CurriculumEdge.space_id.in_(eligible_space_ids),
                CurriculumEdge.from_node_id.in_(node_ids) | CurriculumEdge.to_node_id.in_(node_ids),
            )
        )
        .scalars()
        .all()
    )

    candidates: list[RetrievalCandidate] = []
    rank = 1
    for edge in edges:
        # Confirmed edges rank ahead of suggested.
        base_rank = rank if edge.confirmation == "confirmed" else rank + 100
        related_id = edge.to_node_id if edge.from_node_id in node_ids else edge.from_node_id
        related = next((n for n in nodes if n.id == related_id), None)
        snippet = related.title if related else edge.edge_kind
        candidates.append(
            RetrievalCandidate(
                candidate_id=f"graph:edge:{edge.id}",
                canonical_type="curriculum_edge",
                canonical_id=edge.id,
                revision_id=edge.id,
                space_id=edge.space_id,
                lane=CandidateLane.GRAPH,
                rank=base_rank,
                snippet=f"{edge.confirmation}:{snippet}"[:512],
                score_hint=1.0 if edge.confirmation == "confirmed" else 0.4,
            )
        )
        rank += 1
        if len(candidates) >= max_results:
            break

    # Also surface memory assertions that mention the query as weak graph-adjacent hits.
    if len(candidates) < max_results:
        memories = (
            db.execute(
                select(MemoryRevision).where(
                    MemoryRevision.account_id == ctx.account_id,
                    MemoryRevision.space_id.in_(eligible_space_ids),
                    MemoryRevision.status == "active",
                )
            )
            .scalars()
            .all()
        )
        for memory in memories:
            if trimmed not in memory.assertion_text.lower():
                continue
            if memory.status == "pending" or memory.status == "retracted":
                continue
            candidates.append(
                RetrievalCandidate(
                    candidate_id=f"graph:memory:{memory.memory_item_id}:{memory.id}",
                    canonical_type="memory",
                    canonical_id=memory.memory_item_id,
                    revision_id=memory.id,
                    space_id=memory.space_id,
                    lane=CandidateLane.GRAPH,
                    rank=rank,
                    snippet=memory.assertion_text[:512],
                )
            )
            rank += 1
            if len(candidates) >= max_results:
                break
    return candidates
