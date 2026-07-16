"""Memory items and proposal lifecycle service."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from memdot_domain.ids import new_uuid7
from memdot_domain.memory import MemoryRevisionStatus, memory_truth_class_for_proposal
from memdot_domain.tenancy import ProposalStatus, TruthClass
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import (
    CurrentMemoryRevision,
    MemoryItem,
    MemoryRevision,
    Proposal,
)
from memdot_core.db.tenant import set_current_memory_revision, tenant_scope
from memdot_core.jobs.service import payload_sha256
from memdot_core.request_context import RequestContext


@dataclass(frozen=True)
class MemoryItemResult:
    memory_item_id: uuid.UUID
    space_id: uuid.UUID


@dataclass(frozen=True)
class ProposalResult:
    proposal_id: uuid.UUID
    status: str


def _assertion_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_memory_item(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID,
    title: str,
    assertion_text: str,
) -> MemoryItemResult:
    item_id = new_uuid7()
    revision_id = new_uuid7()
    pointer_id = new_uuid7()
    event_id = new_uuid7()
    digest = _assertion_sha256(assertion_text)
    outbox_payload = {
        "memory_item_id": str(item_id),
        "revision_id": str(revision_id),
        "space_id": str(space_id),
    }
    with tenant_scope(db, ctx.tenant()):
        db.add(
            MemoryItem(
                id=item_id,
                account_id=ctx.account_id,
                space_id=space_id,
                title=title,
            )
        )
        db.add(
            MemoryRevision(
                id=revision_id,
                account_id=ctx.account_id,
                space_id=space_id,
                memory_item_id=item_id,
                base_revision_id=None,
                assertion_text=assertion_text,
                truth_class=TruthClass.USER_ASSERTION.value,
                status=MemoryRevisionStatus.ACTIVE.value,
                content_sha256=digest,
                provenance_json={"author_actor_id": str(ctx.actor_id)},
            )
        )
        set_current_memory_revision(
            db,
            pointer_id=pointer_id,
            account_id=ctx.account_id,
            space_id=space_id,
            memory_item_id=item_id,
            revision_id=revision_id,
            event_id=event_id,
            payload_sha256=payload_sha256(outbox_payload),
            payload_json=json.dumps(outbox_payload),
        )
    return MemoryItemResult(memory_item_id=item_id, space_id=space_id)


def create_proposal(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID,
    target_type: str,
    target_id: uuid.UUID,
    patch_json: dict[str, Any],
    base_revision_id: uuid.UUID | None = None,
) -> ProposalResult:
    proposal_id = new_uuid7()
    with tenant_scope(db, ctx.tenant()):
        db.add(
            Proposal(
                id=proposal_id,
                account_id=ctx.account_id,
                space_id=space_id,
                target_type=target_type,
                target_id=target_id,
                base_revision_id=base_revision_id,
                truth_class=TruthClass.DERIVED_PROPOSAL.value,
                status=ProposalStatus.PENDING.value,
                patch_json=patch_json,
            )
        )
    return ProposalResult(proposal_id=proposal_id, status=ProposalStatus.PENDING.value)


def resolve_proposal(
    db: Session,
    ctx: RequestContext,
    *,
    proposal_id: uuid.UUID,
    approve: bool,
) -> ProposalResult:
    proposal = db.execute(
        select(Proposal).where(
            Proposal.account_id == ctx.account_id,
            Proposal.id == proposal_id,
        )
    ).scalar_one()
    if proposal.status != ProposalStatus.PENDING.value:
        return ProposalResult(proposal_id=proposal_id, status=proposal.status)

    new_status = ProposalStatus.APPROVED if approve else ProposalStatus.REJECTED
    with tenant_scope(db, ctx.tenant()):
        proposal.status = new_status.value
        proposal.resolved_at = datetime.now(UTC)

        if approve and proposal.target_type == "memory_item":
            patch = proposal.patch_json or {}
            assertion = str(patch.get("assertion_text") or "")
            if assertion:
                item_id = proposal.target_id
                item = db.execute(
                    select(MemoryItem).where(
                        MemoryItem.account_id == ctx.account_id,
                        MemoryItem.id == item_id,
                    )
                ).scalar_one()
                current = db.execute(
                    select(CurrentMemoryRevision).where(
                        CurrentMemoryRevision.account_id == ctx.account_id,
                        CurrentMemoryRevision.memory_item_id == item_id,
                    )
                ).scalar_one_or_none()
                base_id = current.revision_id if current else None
                revision_id = new_uuid7()
                pointer_id = current.id if current else new_uuid7()
                event_id = new_uuid7()
                digest = _assertion_sha256(assertion)
                outbox_payload = {
                    "memory_item_id": str(item_id),
                    "revision_id": str(revision_id),
                    "space_id": str(item.space_id),
                    "proposal_id": str(proposal_id),
                }
                db.add(
                    MemoryRevision(
                        id=revision_id,
                        account_id=ctx.account_id,
                        space_id=item.space_id,
                        memory_item_id=item_id,
                        base_revision_id=base_id,
                        assertion_text=assertion,
                        truth_class=memory_truth_class_for_proposal(approved=True).value,
                        status=MemoryRevisionStatus.ACTIVE.value,
                        content_sha256=digest,
                        provenance_json={"proposal_id": str(proposal_id)},
                    )
                )
                set_current_memory_revision(
                    db,
                    pointer_id=pointer_id,
                    account_id=ctx.account_id,
                    space_id=item.space_id,
                    memory_item_id=item_id,
                    revision_id=revision_id,
                    event_id=event_id,
                    payload_sha256=payload_sha256(outbox_payload),
                    payload_json=json.dumps(outbox_payload),
                )

    return ProposalResult(proposal_id=proposal_id, status=new_status.value)


def get_memory_item(
    db: Session,
    ctx: RequestContext,
    *,
    memory_item_id: uuid.UUID,
) -> dict[str, Any] | None:
    item = db.execute(
        select(MemoryItem).where(
            MemoryItem.account_id == ctx.account_id,
            MemoryItem.id == memory_item_id,
        )
    ).scalar_one_or_none()
    if item is None:
        return None
    current = db.execute(
        select(CurrentMemoryRevision).where(
            CurrentMemoryRevision.account_id == ctx.account_id,
            CurrentMemoryRevision.memory_item_id == memory_item_id,
        )
    ).scalar_one_or_none()
    revision = None
    if current is not None:
        revision = db.execute(
            select(MemoryRevision).where(
                MemoryRevision.account_id == ctx.account_id,
                MemoryRevision.id == current.revision_id,
            )
        ).scalar_one_or_none()
    return {
        "memoryItemId": str(item.id),
        "spaceId": str(item.space_id),
        "title": item.title,
        "currentRevision": {
            "revisionId": str(revision.id),
            "assertionText": revision.assertion_text,
            "truthClass": revision.truth_class,
            "status": revision.status,
            "contentSha256": revision.content_sha256,
        }
        if revision
        else None,
    }
