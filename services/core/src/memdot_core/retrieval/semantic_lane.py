"""Local deterministic semantic lane (bag-of-words hash embedding; rebuildable)."""

from __future__ import annotations

import hashlib
import math
import re
import uuid
from collections import Counter

from memdot_domain.retrieval import CandidateLane, RetrievalCandidate
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import DocumentRevision, MemoryRevision
from memdot_core.request_context import RequestContext

_TOKEN_RE = re.compile(r"[\w\u0900-\u097F]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text) if token.strip()]


def embedding_hash(text: str, *, dims: int = 64) -> list[float]:
    """Deterministic sparse bag-of-words hashed into a fixed vector."""
    counts = Counter(tokenize(text))
    if not counts:
        return [0.0] * dims
    vec = [0.0] * dims
    for token, count in counts.items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dims
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vec[index] += sign * float(count)
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def semantic_candidates(
    db: Session,
    ctx: RequestContext,
    *,
    query: str,
    eligible_space_ids: set[uuid.UUID],
    as_of: object | None = None,
    max_results: int = 20,
    min_score: float = 0.15,
) -> list[RetrievalCandidate]:
    trimmed = query.strip()
    if not trimmed or not eligible_space_ids:
        return []
    query_vec = embedding_hash(trimmed)
    scored: list[tuple[float, RetrievalCandidate]] = []

    doc_query = select(DocumentRevision).where(
        DocumentRevision.account_id == ctx.account_id,
        DocumentRevision.space_id.in_(eligible_space_ids),
        DocumentRevision.plain_text.is_not(None),
    )
    if as_of is not None:
        doc_query = doc_query.where(DocumentRevision.created_at <= as_of)  # type: ignore[operator]

    for revision in db.execute(doc_query).scalars():
        text = revision.plain_text or ""
        if not text:
            continue
        score = cosine(query_vec, embedding_hash(text))
        if score < min_score:
            continue
        scored.append(
            (
                score,
                RetrievalCandidate(
                    candidate_id=f"semantic:document:{revision.document_id}:{revision.id}",
                    canonical_type="document",
                    canonical_id=revision.document_id,
                    revision_id=revision.id,
                    space_id=revision.space_id,
                    lane=CandidateLane.OSS_SEMANTIC,
                    rank=1,
                    snippet=text[:512],
                    score_hint=score,
                ),
            )
        )

    mem_query = select(MemoryRevision).where(
        MemoryRevision.account_id == ctx.account_id,
        MemoryRevision.space_id.in_(eligible_space_ids),
        MemoryRevision.status == "active",
    )
    if as_of is not None:
        mem_query = mem_query.where(MemoryRevision.created_at <= as_of)  # type: ignore[operator]

    for memory in db.execute(mem_query).scalars():
        score = cosine(query_vec, embedding_hash(memory.assertion_text))
        if score < min_score:
            continue
        scored.append(
            (
                score,
                RetrievalCandidate(
                    candidate_id=f"semantic:memory:{memory.memory_item_id}:{memory.id}",
                    canonical_type="memory",
                    canonical_id=memory.memory_item_id,
                    revision_id=memory.id,
                    space_id=memory.space_id,
                    lane=CandidateLane.OSS_SEMANTIC,
                    rank=1,
                    snippet=memory.assertion_text[:512],
                    score_hint=score,
                ),
            )
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    results: list[RetrievalCandidate] = []
    for index, (_score, candidate) in enumerate(scored[:max_results], start=1):
        results.append(
            RetrievalCandidate(
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
        )
    return results
