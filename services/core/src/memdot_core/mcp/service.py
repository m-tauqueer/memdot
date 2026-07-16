"""MCP search/fetch and external tool backing services."""

from __future__ import annotations

import uuid
from typing import Any

from memdot_domain.ids import new_uuid7
from memdot_domain.mcp import (
    citation_url,
    decode_mcp_public_id,
    encode_mcp_public_id,
    map_mcp_completeness_to_conversation,
)
from memdot_domain.retrieval import CandidateLane, exclude_private_spaces, fuse_candidates
from memdot_domain.tenancy import RequestPurpose, SpaceVisibility, TruthClass
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.context import service as context_service
from memdot_core.context.service import local_candidates
from memdot_core.conversations.crypto import decrypt_payload, encrypt_payload, payload_content
from memdot_core.db.models.ledger import (
    AuthoredDocument,
    Conversation,
    ConversationTurn,
    CurrentDocumentRevision,
    CurriculumEdge,
    DocumentRevision,
    MemoryItem,
    MemoryRevision,
)
from memdot_core.db.models.tenancy import Space
from memdot_core.db.tenant import tenant_scope
from memdot_core.deletion import service as deletion_service
from memdot_core.errors import ErrorCode
from memdot_core.memory import service as memory_service
from memdot_core.request_context import RequestContext
from memdot_core.retrieval.filters import (
    filter_pending_and_retracted,
    filter_private_spaces,
    filter_tombstoned,
)
from memdot_core.retrieval.graph_lane import graph_candidates
from memdot_core.retrieval.semantic_lane import semantic_candidates
from memdot_core.retrieval.temporal_lane import temporal_candidates


def _space_visibility_map(db: Session, account_id: uuid.UUID) -> dict[uuid.UUID, SpaceVisibility]:
    rows = db.execute(select(Space).where(Space.account_id == account_id)).scalars().all()
    return {row.id: SpaceVisibility(row.visibility) for row in rows}


def _eligible_non_private_spaces(
    ctx: RequestContext, visibilities: dict[uuid.UUID, SpaceVisibility]
) -> set[uuid.UUID]:
    # External contexts always carry an explicit eligible set (possibly empty).
    # Empty means no access — never expand to all Spaces.
    from memdot_domain.tenancy import RequestPurpose as RP

    if ctx.purpose in {
        RP.EXTERNAL_READ,
        RP.EXTERNAL_PROPOSE,
        RP.EXTERNAL_INTERACTION,
    }:
        eligible = set(ctx.eligible_space_ids)
    else:
        eligible = (
            set(ctx.eligible_space_ids) if ctx.eligible_space_ids else set(visibilities.keys())
        )
    return {
        space_id
        for space_id in eligible
        if visibilities.get(space_id, SpaceVisibility.GENERAL) != SpaceVisibility.PRIVATE
    }


def _is_entity_available(
    db: Session,
    *,
    account_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
) -> bool:
    return not deletion_service.is_tombstoned(
        db, account_id=account_id, entity_type=entity_type, entity_id=entity_id
    )


def search(
    db: Session,
    ctx: RequestContext,
    *,
    query: str,
    public_base_url: str,
    max_results: int = 20,
    as_of: object | None = None,
) -> dict[str, Any]:
    """Company-knowledge-compatible search over eligible non-private account."""
    trimmed = query.strip()
    if not trimmed or len(trimmed) > 2048:
        return {"results": []}

    visibilities = _space_visibility_map(db, ctx.account_id)
    eligible = _eligible_non_private_spaces(ctx, visibilities)
    exact, _corpus = local_candidates(db, ctx, query=trimmed, eligible_space_ids=eligible)
    graph = graph_candidates(db, ctx, query=trimmed, eligible_space_ids=eligible)
    semantic = semantic_candidates(db, ctx, query=trimmed, eligible_space_ids=eligible, as_of=as_of)
    temporal = temporal_candidates(
        db,
        ctx,
        query=trimmed,
        eligible_space_ids=eligible,
        as_of=as_of,  # type: ignore[arg-type]
    )
    fused = fuse_candidates(
        {
            CandidateLane.TEMPORAL_EXACT: temporal,
            CandidateLane.EXACT: exact,
            CandidateLane.GRAPH: graph,
            CandidateLane.OSS_SEMANTIC: semantic,
        }
    )
    fused = exclude_private_spaces(
        fused, space_visibility=visibilities, purpose=RequestPurpose.EXTERNAL_READ.value
    )
    fused = filter_private_spaces(db, account_id=ctx.account_id, candidates=fused)
    fused = filter_tombstoned(db, account_id=ctx.account_id, candidates=fused)
    fused = filter_pending_and_retracted(db, account_id=ctx.account_id, candidates=fused)

    results: list[dict[str, str]] = []
    for item in fused[:max_results]:
        if not _is_entity_available(
            db,
            account_id=ctx.account_id,
            entity_type=item.canonical_type,
            entity_id=item.canonical_id,
        ):
            continue
        mcp_id = encode_mcp_public_id(
            item.canonical_type, item.canonical_id, revision_id=item.revision_id
        )
        title = item.snippet[:120] if item.snippet else item.canonical_type
        results.append(
            {
                "id": mcp_id,
                "title": title,
                "url": citation_url(public_base_url, item.canonical_type, item.canonical_id),
            }
        )
    return {"results": results}


def fetch(
    db: Session,
    ctx: RequestContext,
    *,
    mcp_id: str,
    public_base_url: str,
) -> dict[str, Any] | None:
    """Company-knowledge-compatible fetch for a single MCP public id."""
    try:
        canonical_type, canonical_id, revision_id = decode_mcp_public_id(mcp_id)
    except ValueError:
        return None

    if not _is_entity_available(
        db,
        account_id=ctx.account_id,
        entity_type=canonical_type,
        entity_id=canonical_id,
    ):
        return None

    visibilities = _space_visibility_map(db, ctx.account_id)

    if canonical_type == "document":
        return _fetch_document(
            db,
            ctx,
            document_id=canonical_id,
            revision_id=revision_id,
            public_base_url=public_base_url,
            visibilities=visibilities,
        )
    if canonical_type == "memory":
        return _fetch_memory(
            db,
            ctx,
            memory_item_id=canonical_id,
            revision_id=revision_id,
            public_base_url=public_base_url,
            visibilities=visibilities,
        )
    if canonical_type == "document_element":
        return _fetch_element(
            db,
            ctx,
            element_id=canonical_id,
            public_base_url=public_base_url,
            mcp_id=mcp_id,
            visibilities=visibilities,
        )
    if canonical_type == "curriculum_edge":
        return _fetch_curriculum_edge(
            db,
            ctx,
            edge_id=canonical_id,
            public_base_url=public_base_url,
            mcp_id=mcp_id,
            visibilities=visibilities,
        )
    return None


def _space_is_private(visibilities: dict[uuid.UUID, SpaceVisibility], space_id: uuid.UUID) -> bool:
    return visibilities.get(space_id, SpaceVisibility.GENERAL) == SpaceVisibility.PRIVATE


def _fetch_document(
    db: Session,
    ctx: RequestContext,
    *,
    document_id: uuid.UUID,
    revision_id: uuid.UUID | None,
    public_base_url: str,
    visibilities: dict[uuid.UUID, SpaceVisibility],
) -> dict[str, Any] | None:
    doc = db.execute(
        select(AuthoredDocument).where(
            AuthoredDocument.account_id == ctx.account_id,
            AuthoredDocument.id == document_id,
        )
    ).scalar_one_or_none()
    if doc is None:
        return None
    if _space_is_private(visibilities, doc.space_id):
        return None

    rev_query = select(DocumentRevision).where(
        DocumentRevision.account_id == ctx.account_id,
        DocumentRevision.document_id == document_id,
    )
    if revision_id:
        rev_query = rev_query.where(DocumentRevision.id == revision_id)
    else:
        current = db.execute(
            select(CurrentDocumentRevision).where(
                CurrentDocumentRevision.account_id == ctx.account_id,
                CurrentDocumentRevision.document_id == document_id,
            )
        ).scalar_one_or_none()
        if current:
            rev_query = rev_query.where(DocumentRevision.id == current.revision_id)

    revision = db.execute(rev_query).scalars().first()
    if revision is None:
        return None

    text = revision.plain_text or ""
    mcp_id = encode_mcp_public_id("document", document_id, revision_id=revision.id)
    return {
        "id": mcp_id,
        "title": doc.title,
        "text": text,
        "url": citation_url(public_base_url, "document", document_id),
        "metadata": {
            "canonicalType": "document",
            "revisionId": str(revision.id),
            "truthClass": TruthClass.USER_ASSERTION.value,
        },
    }


def _fetch_memory(
    db: Session,
    ctx: RequestContext,
    *,
    memory_item_id: uuid.UUID,
    revision_id: uuid.UUID | None,
    public_base_url: str,
    visibilities: dict[uuid.UUID, SpaceVisibility],
) -> dict[str, Any] | None:
    item = db.execute(
        select(MemoryItem).where(
            MemoryItem.account_id == ctx.account_id,
            MemoryItem.id == memory_item_id,
        )
    ).scalar_one_or_none()
    if item is None:
        return None
    if _space_is_private(visibilities, item.space_id):
        return None

    rev_query = select(MemoryRevision).where(
        MemoryRevision.account_id == ctx.account_id,
        MemoryRevision.memory_item_id == memory_item_id,
        MemoryRevision.status == "active",
    )
    if revision_id:
        rev_query = rev_query.where(MemoryRevision.id == revision_id)
    revision = db.execute(rev_query).scalars().first()
    if revision is None:
        return None

    mcp_id = encode_mcp_public_id("memory", memory_item_id, revision_id=revision.id)
    return {
        "id": mcp_id,
        "title": item.title,
        "text": revision.assertion_text,
        "url": citation_url(public_base_url, "memory", memory_item_id),
        "metadata": {
            "canonicalType": "memory",
            "revisionId": str(revision.id),
            "truthClass": revision.truth_class,
        },
    }


def _fetch_element(
    db: Session,
    ctx: RequestContext,
    *,
    element_id: uuid.UUID,
    public_base_url: str,
    mcp_id: str,
    visibilities: dict[uuid.UUID, SpaceVisibility],
) -> dict[str, Any] | None:
    from memdot_core.db.models.ledger import DocumentElement

    element = db.execute(
        select(DocumentElement).where(
            DocumentElement.account_id == ctx.account_id,
            DocumentElement.id == element_id,
        )
    ).scalar_one_or_none()
    if element is None:
        return None
    if _space_is_private(visibilities, element.space_id):
        return None
    text = element.exact_text or ""
    return {
        "id": mcp_id,
        "title": element.element_kind,
        "text": text,
        "url": citation_url(public_base_url, "document_element", element_id),
        "metadata": {
            "canonicalType": "document_element",
            "revisionId": str(element_id),
            "locator": element.locator,
        },
    }


def _fetch_curriculum_edge(
    db: Session,
    ctx: RequestContext,
    *,
    edge_id: uuid.UUID,
    public_base_url: str,
    mcp_id: str,
    visibilities: dict[uuid.UUID, SpaceVisibility],
) -> dict[str, Any] | None:
    edge = db.execute(
        select(CurriculumEdge).where(
            CurriculumEdge.account_id == ctx.account_id, CurriculumEdge.id == edge_id
        )
    ).scalar_one_or_none()
    if edge is None or _space_is_private(visibilities, edge.space_id):
        return None
    return {
        "id": mcp_id,
        "title": f"{edge.edge_kind} relationship",
        "text": f"{edge.from_node_id} {edge.edge_kind} {edge.to_node_id}",
        "url": citation_url(public_base_url, "curriculum_edge", edge_id),
        "metadata": {
            "canonicalType": "curriculum_edge",
            "revisionId": str(edge.id),
            "confirmation": edge.confirmation,
        },
    }


def prepare_context(
    db: Session,
    ctx: RequestContext,
    *,
    query: str,
    purpose: str | None = None,
    max_tokens: int = 4096,
    max_items: int = 32,
) -> dict[str, Any]:
    external_ctx = RequestContext(
        account_id=ctx.account_id,
        actor_id=ctx.actor_id,
        user_id=ctx.user_id,
        purpose=RequestPurpose.EXTERNAL_READ,
        correlation_id=ctx.correlation_id,
        scopes=ctx.scopes,
        eligible_space_ids=ctx.eligible_space_ids,
        last_auth_at=ctx.last_auth_at,
    )
    return context_service.compile_context_for_request(
        db,
        external_ctx,
        query=query,
        purpose=purpose or "general",
        max_tokens=max_tokens,
        max_items=max_items,
    )


def propose_memory(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID,
    assertion_text: str,
    title: str = "MCP proposal",
    target_type: str = "memory",
    target_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    target = target_id or new_uuid7()
    external_ctx = RequestContext(
        account_id=ctx.account_id,
        actor_id=ctx.actor_id,
        user_id=ctx.user_id,
        purpose=RequestPurpose.EXTERNAL_PROPOSE,
        correlation_id=ctx.correlation_id,
        scopes=ctx.scopes,
        eligible_space_ids=ctx.eligible_space_ids,
    )
    visibilities = _space_visibility_map(db, ctx.account_id)
    if visibilities.get(space_id) == SpaceVisibility.PRIVATE:
        msg = "private space excluded"
        raise ValueError(msg)

    created = memory_service.create_proposal(
        db,
        external_ctx,
        space_id=space_id,
        target_type=target_type,
        target_id=target,
        patch_json={"assertion_text": assertion_text, "title": title},
    )
    return {"proposalId": str(created.proposal_id), "status": created.status}


def record_interaction(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID,
    client_conversation_id: str,
    role: str,
    content: str,
    completeness: str,
    context_receipt_id: uuid.UUID | None = None,
    idempotency_key: str | None = None,
    client_turn_id: str | None = None,
    parent_turn_id: uuid.UUID | None = None,
    occurred_at: object | None = None,
) -> dict[str, Any]:
    """Append explicit external turn; never mutates learner evidence."""
    from datetime import UTC, datetime

    visibilities = _space_visibility_map(db, ctx.account_id)
    if visibilities.get(space_id) == SpaceVisibility.PRIVATE:
        msg = "private space excluded"
        raise ValueError(msg)
    if role not in {"user", "assistant", "system", "tool"}:
        msg = "invalid_role"
        raise ValueError(msg)
    if len(content) > 65536:
        msg = "content_too_large"
        raise ValueError(msg)

    external_ctx = RequestContext(
        account_id=ctx.account_id,
        actor_id=ctx.actor_id,
        user_id=ctx.user_id,
        purpose=RequestPurpose.EXTERNAL_INTERACTION,
        correlation_id=ctx.correlation_id,
        scopes=ctx.scopes,
        eligible_space_ids=ctx.eligible_space_ids,
    )
    conversation_label = map_mcp_completeness_to_conversation(completeness).value
    turn_key = client_turn_id or idempotency_key
    ciphertext, nonce = encrypt_payload({"content": content})
    occurred = occurred_at if isinstance(occurred_at, datetime) else datetime.now(UTC)

    with tenant_scope(db, external_ctx.tenant()):
        conversation = db.execute(
            select(Conversation).where(
                Conversation.account_id == ctx.account_id,
                Conversation.space_id == space_id,
                Conversation.source_client == client_conversation_id,
            )
        ).scalar_one_or_none()
        if conversation is None:
            conversation_id = new_uuid7()
            db.add(
                Conversation(
                    id=conversation_id,
                    account_id=ctx.account_id,
                    space_id=space_id,
                    source_client=client_conversation_id,
                    completeness=conversation_label,
                )
            )
            turn_index = 0
        else:
            conversation_id = conversation.id
            if deletion_service.is_tombstoned(
                db,
                account_id=ctx.account_id,
                entity_type="conversation",
                entity_id=conversation_id,
            ):
                msg = "conversation tombstoned"
                raise ValueError(msg)
            last_turn = db.execute(
                select(ConversationTurn.turn_index)
                .where(
                    ConversationTurn.account_id == ctx.account_id,
                    ConversationTurn.conversation_id == conversation_id,
                )
                .order_by(ConversationTurn.turn_index.desc())
            ).scalar_one_or_none()
            turn_index = (last_turn or -1) + 1

        if turn_key:
            existing = db.execute(
                select(ConversationTurn).where(
                    ConversationTurn.account_id == ctx.account_id,
                    ConversationTurn.conversation_id == conversation_id,
                    ConversationTurn.client_turn_id == turn_key,
                )
            ).scalar_one_or_none()
            if existing is not None:
                existing_content = (
                    payload_content(
                        decrypt_payload(existing.payload_ciphertext, existing.payload_nonce)
                    )
                    if existing.payload_ciphertext and existing.payload_nonce
                    else payload_content(existing.payload_json)
                )
                if (
                    existing.role != role
                    or existing_content != content
                    or existing.parent_turn_id != parent_turn_id
                    or existing.context_receipt_id != context_receipt_id
                    or existing.occurred_at != occurred
                ):
                    raise ValueError(ErrorCode.IDEMPOTENCY_CONFLICT.value)
                return {
                    "conversationId": str(conversation_id),
                    "turnId": str(existing.id),
                    "turnIndex": existing.turn_index,
                    "completeness": conversation_label,
                    "learnerEvidenceChanged": False,
                    "idempotent": True,
                }

        turn_id = new_uuid7()
        db.add(
            ConversationTurn(
                id=turn_id,
                account_id=ctx.account_id,
                space_id=space_id,
                conversation_id=conversation_id,
                role=role,
                turn_index=turn_index,
                # Never store plaintext interaction content in payload_json.
                payload_json={"encrypted": True},
                payload_ciphertext=ciphertext,
                payload_nonce=nonce,
                occurred_at=occurred,
                parent_turn_id=parent_turn_id,
                context_receipt_id=context_receipt_id,
                client_turn_id=turn_key or f"{client_conversation_id}:{turn_index}",
            )
        )

    # Learner evidence is intentionally untouched — no learner_event writes.

    return {
        "conversationId": str(conversation_id),
        "turnId": str(turn_id),
        "turnIndex": turn_index,
        "completeness": conversation_label,
        "learnerEvidenceChanged": False,
        "idempotent": False,
    }
