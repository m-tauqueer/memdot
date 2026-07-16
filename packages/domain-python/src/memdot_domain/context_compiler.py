"""Context compiler: budget packing, omissions, and receipt structure."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from memdot_domain.retrieval import FusedCandidate


class OmitReason(StrEnum):
    BUDGET = "budget_exceeded"
    PRIVATE = "private_space_excluded"
    RETRACTED = "retracted"
    STALE = "stale_revision"
    DUPLICATE = "duplicate"
    POLICY = "policy_excluded"


@dataclass(frozen=True)
class ContextBudget:
    max_tokens: int = 4096
    max_items: int = 32

    def char_budget(self) -> int:
        # Rough chars-per-token estimate for packing heuristics.
        return self.max_tokens * 4


@dataclass
class EvidenceItem:
    rank: int
    canonical_type: str
    canonical_id: uuid.UUID
    revision_id: uuid.UUID
    locator: str | None
    text: str
    selected: bool
    omit_reason: OmitReason | None = None


@dataclass
class ContextReceipt:
    receipt_id: uuid.UUID
    query_hash: str
    purpose: str
    policy_version: str
    eligible_spaces: list[uuid.UUID]
    provider_versions: dict[str, str]
    budget: ContextBudget
    context_hash: str
    partial: bool
    items: list[EvidenceItem] = field(default_factory=lambda: [])


def query_hash(query: str, *, purpose: str, policy_version: str) -> str:
    payload = json.dumps(
        {"query": query.strip(), "purpose": purpose, "policy_version": policy_version},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def context_hash(items: list[EvidenceItem]) -> str:
    canonical = [
        {
            "rank": item.rank,
            "canonical_type": item.canonical_type,
            "canonical_id": str(item.canonical_id),
            "revision_id": str(item.revision_id),
            "selected": item.selected,
            "omit_reason": item.omit_reason.value if item.omit_reason else None,
        }
        for item in items
    ]
    digest = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(digest.encode("utf-8")).hexdigest()


def compile_context(
    *,
    query: str,
    purpose: str,
    policy_version: str,
    eligible_spaces: list[uuid.UUID],
    provider_versions: dict[str, str],
    candidates: list[FusedCandidate],
    corpus_text: dict[str, str],
    budget: ContextBudget | None = None,
) -> ContextReceipt:
    """Pack fused candidates into a content-minimized receipt (no chain-of-thought)."""
    active_budget = budget or ContextBudget()
    receipt_id = uuid.uuid4()
    q_hash = query_hash(query, purpose=purpose, policy_version=policy_version)
    items: list[EvidenceItem] = []
    used_chars = 0
    seen: set[str] = set()
    char_limit = active_budget.char_budget()

    for rank, candidate in enumerate(candidates, start=1):
        key = candidate.candidate_id
        text = corpus_text.get(key, candidate.snippet or "")
        omit: OmitReason | None = None
        selected = True

        if key in seen:
            selected = False
            omit = OmitReason.DUPLICATE
        elif len([i for i in items if i.selected]) >= active_budget.max_items:
            selected = False
            omit = OmitReason.BUDGET
        elif used_chars + len(text) > char_limit:
            selected = False
            omit = OmitReason.BUDGET
        else:
            seen.add(key)
            used_chars += len(text)

        items.append(
            EvidenceItem(
                rank=rank,
                canonical_type=candidate.canonical_type,
                canonical_id=candidate.canonical_id,
                revision_id=candidate.revision_id,
                locator=candidate.locator,
                text=text if selected else "",
                selected=selected,
                omit_reason=omit,
            )
        )

    partial = any(not item.selected for item in items)
    return ContextReceipt(
        receipt_id=receipt_id,
        query_hash=q_hash,
        purpose=purpose,
        policy_version=policy_version,
        eligible_spaces=eligible_spaces,
        provider_versions=provider_versions,
        budget=active_budget,
        context_hash=context_hash(items),
        partial=partial,
        items=items,
    )
