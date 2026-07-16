"""Context compile service over local canonical candidates."""

from __future__ import annotations

import uuid
from typing import Any

from memdot_domain.context_compiler import ContextBudget, compile_context
from memdot_domain.ids import new_uuid7
from memdot_domain.retrieval import (
    CandidateLane,
    RetrievalCandidate,
    exclude_private_spaces,
    fuse_candidates,
)
from memdot_domain.tenancy import RequestPurpose, SpaceVisibility
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import (
    ContextReceipt,
    ContextReceiptItem,
    DocumentElement,
    DocumentRevision,
    MemoryRevision,
)
from memdot_core.db.models.tenancy import Space
from memdot_core.db.tenant import tenant_scope
from memdot_core.request_context import RequestContext

POLICY_VERSION = "context-compiler-v1"


def _space_visibility_map(db: Session, account_id: uuid.UUID) -> dict[uuid.UUID, SpaceVisibility]:
    rows = db.execute(select(Space).where(Space.account_id == account_id)).scalars().all()
    return {row.id: SpaceVisibility(row.visibility) for row in rows}


def _local_candidates(
    db: Session,
    ctx: RequestContext,
    *,
    query: str,
    eligible_space_ids: set[uuid.UUID],
) -> tuple[list[RetrievalCandidate], dict[str, str]]:
    corpus: dict[str, str] = {}
    candidates: list[RetrievalCandidate] = []

    doc_revisions = db.execute(
        select(DocumentRevision).where(
            DocumentRevision.account_id == ctx.account_id,
            DocumentRevision.space_id.in_(eligible_space_ids),
            DocumentRevision.plain_text.is_not(None),
        )
    ).scalars()
    rank = 1
    for revision in doc_revisions:
        text = revision.plain_text or ""
        if not text:
            continue
        candidate_id = f"document:{revision.document_id}:{revision.id}"
        corpus[candidate_id] = text
        candidates.append(
            RetrievalCandidate(
                candidate_id=candidate_id,
                canonical_type="document",
                canonical_id=revision.document_id,
                revision_id=revision.id,
                space_id=revision.space_id,
                lane=CandidateLane.EXACT,
                rank=rank,
                snippet=text[:512],
            )
        )
        rank += 1

    memory_rows = db.execute(
        select(MemoryRevision).where(
            MemoryRevision.account_id == ctx.account_id,
            MemoryRevision.space_id.in_(eligible_space_ids),
            MemoryRevision.status == "active",
        )
    ).scalars()
    for row in memory_rows:
        candidate_id = f"memory:{row.memory_item_id}:{row.id}"
        corpus[candidate_id] = row.assertion_text
        candidates.append(
            RetrievalCandidate(
                candidate_id=candidate_id,
                canonical_type="memory",
                canonical_id=row.memory_item_id,
                revision_id=row.id,
                space_id=row.space_id,
                lane=CandidateLane.EXACT,
                rank=rank,
                snippet=row.assertion_text[:512],
            )
        )
        rank += 1

    elements = db.execute(
        select(DocumentElement).where(
            DocumentElement.account_id == ctx.account_id,
            DocumentElement.space_id.in_(eligible_space_ids),
            DocumentElement.exact_text.is_not(None),
        )
    ).scalars()
    for element in elements:
        text = element.exact_text or ""
        if not text:
            continue
        candidate_id = f"element:{element.id}"
        corpus[candidate_id] = text
        candidates.append(
            RetrievalCandidate(
                candidate_id=candidate_id,
                canonical_type="document_element",
                canonical_id=element.id,
                revision_id=element.id,
                space_id=element.space_id,
                lane=CandidateLane.EXACT,
                rank=rank,
                locator=element.locator,
                snippet=text[:512],
            )
        )
        rank += 1

    query_lower = query.lower()
    if query_lower:
        matched = [
            candidate
            for candidate in candidates
            if query_lower in (corpus.get(candidate.candidate_id) or "").lower()
        ]
        if matched:
            candidates = [
                RetrievalCandidate(
                    candidate_id=item.candidate_id,
                    canonical_type=item.canonical_type,
                    canonical_id=item.canonical_id,
                    revision_id=item.revision_id,
                    space_id=item.space_id,
                    lane=item.lane,
                    rank=index,
                    locator=item.locator,
                    snippet=item.snippet,
                    score_hint=item.score_hint,
                )
                for index, item in enumerate(matched, start=1)
            ]

    return candidates, corpus


def compile_context_for_request(
    db: Session,
    ctx: RequestContext,
    *,
    query: str,
    purpose: str | None = None,
    max_tokens: int = 4096,
    max_items: int = 32,
) -> dict[str, Any]:
    active_purpose = purpose or ctx.purpose.value
    visibilities = _space_visibility_map(db, ctx.account_id)
    eligible = set(ctx.eligible_space_ids) if ctx.eligible_space_ids else set(visibilities.keys())
    if active_purpose == RequestPurpose.EXTERNAL_READ.value:
        eligible = {
            space_id
            for space_id in eligible
            if visibilities.get(space_id, SpaceVisibility.GENERAL) != SpaceVisibility.PRIVATE
        }

    raw_candidates, corpus = _local_candidates(
        db, ctx, query=query, eligible_space_ids=eligible
    )
    lane_results = {CandidateLane.EXACT: raw_candidates}
    fused = fuse_candidates(lane_results)
    fused = exclude_private_spaces(fused, space_visibility=visibilities, purpose=active_purpose)

    receipt = compile_context(
        query=query,
        purpose=active_purpose,
        policy_version=POLICY_VERSION,
        eligible_spaces=list(eligible),
        provider_versions={"local_lexical": "v1"},
        candidates=fused,
        corpus_text=corpus,
        budget=ContextBudget(max_tokens=max_tokens, max_items=max_items),
    )

    receipt_id = new_uuid7()
    with tenant_scope(db, ctx.tenant()):
        db.add(
            ContextReceipt(
                id=receipt_id,
                account_id=ctx.account_id,
                query_hash=receipt.query_hash,
                purpose=receipt.purpose,
                policy_version=receipt.policy_version,
                eligible_spaces=[str(space_id) for space_id in receipt.eligible_spaces],
                provider_versions=receipt.provider_versions,
                budget={
                    "max_tokens": receipt.budget.max_tokens,
                    "max_items": receipt.budget.max_items,
                },
                context_hash=receipt.context_hash,
                partial=receipt.partial,
            )
        )
        for item in receipt.items:
            db.add(
                ContextReceiptItem(
                    id=new_uuid7(),
                    account_id=ctx.account_id,
                    receipt_id=receipt_id,
                    rank=item.rank,
                    canonical_type=item.canonical_type,
                    canonical_id=item.canonical_id,
                    revision_id=item.revision_id,
                    locator=item.locator,
                    selected=item.selected,
                    omit_reason=item.omit_reason.value if item.omit_reason else None,
                )
            )

    return {
        "receiptId": str(receipt_id),
        "queryHash": receipt.query_hash,
        "contextHash": receipt.context_hash,
        "partial": receipt.partial,
        "policyVersion": receipt.policy_version,
        "evidence": [
            {
                "rank": item.rank,
                "canonicalType": item.canonical_type,
                "canonicalId": str(item.canonical_id),
                "revisionId": str(item.revision_id),
                "locator": item.locator,
                "text": item.text if item.selected else "",
                "selected": item.selected,
                "omitReason": item.omit_reason.value if item.omit_reason else None,
            }
            for item in receipt.items
        ],
    }
