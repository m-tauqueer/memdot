"""Hard rejoin filters for retrieval candidates."""

from __future__ import annotations

import uuid
from datetime import datetime

from memdot_domain.retrieval import FusedCandidate, RetrievalCandidate
from memdot_domain.tenancy import SpaceVisibility
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import MemoryRevision, Proposal
from memdot_core.db.models.tenancy import Space
from memdot_core.deletion import service as deletion_service


def filter_tombstoned[CandidateT: (FusedCandidate, RetrievalCandidate)](
    db: Session,
    *,
    account_id: uuid.UUID,
    candidates: list[CandidateT],
) -> list[CandidateT]:
    kept: list[CandidateT] = []
    for item in candidates:
        entity_type = item.canonical_type
        entity_id = item.canonical_id
        if deletion_service.is_tombstoned(
            db, account_id=account_id, entity_type=entity_type, entity_id=entity_id
        ):
            continue
        kept.append(item)
    return kept


def filter_private_spaces[CandidateT: (FusedCandidate, RetrievalCandidate)](
    db: Session,
    *,
    account_id: uuid.UUID,
    candidates: list[CandidateT],
    allow_private: bool = False,
) -> list[CandidateT]:
    if allow_private:
        return list(candidates)
    spaces = {
        row.id: SpaceVisibility(row.visibility)
        for row in db.execute(select(Space).where(Space.account_id == account_id)).scalars()
    }
    return [
        item
        for item in candidates
        if spaces.get(item.space_id, SpaceVisibility.GENERAL) != SpaceVisibility.PRIVATE
    ]


def filter_pending_and_retracted[CandidateT: (FusedCandidate, RetrievalCandidate)](
    db: Session,
    *,
    account_id: uuid.UUID,
    candidates: list[CandidateT],
) -> list[CandidateT]:
    pending_targets = {
        row.target_id
        for row in db.execute(
            select(Proposal).where(
                Proposal.account_id == account_id,
                Proposal.status == "pending",
            )
        ).scalars()
    }
    retracted_memory = {
        row.memory_item_id
        for row in db.execute(
            select(MemoryRevision).where(
                MemoryRevision.account_id == account_id,
                MemoryRevision.status == "retracted",
            )
        ).scalars()
    }
    kept: list[CandidateT] = []
    for item in candidates:
        if item.canonical_id in pending_targets:
            continue
        if item.canonical_type == "memory" and item.canonical_id in retracted_memory:
            continue
        kept.append(item)
    return kept


def filter_as_of(
    candidates: list[RetrievalCandidate],
    *,
    revision_created_at: dict[uuid.UUID, datetime],
    as_of: datetime | None,
) -> list[RetrievalCandidate]:
    if as_of is None:
        return candidates
    return [
        item
        for item in candidates
        if revision_created_at.get(item.revision_id) is None
        or revision_created_at[item.revision_id] <= as_of
    ]
