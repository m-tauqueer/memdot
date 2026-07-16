"""Memory ontology, proposal status, and truth-class helpers."""

from __future__ import annotations

from enum import StrEnum

from memdot_domain.tenancy import ProposalStatus, TruthClass


class MemoryAssertionType(StrEnum):
    FACT = "fact"
    RELATIONSHIP = "relationship"
    SUMMARY = "summary"
    DEFINITION = "definition"


class MemoryRevisionStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"


RETRIEVABLE_PROPOSAL_STATUSES = frozenset({ProposalStatus.APPROVED})
EXCLUDED_PROPOSAL_STATUSES = frozenset(
    {
        ProposalStatus.PENDING,
        ProposalStatus.REJECTED,
        ProposalStatus.EXPIRED,
        ProposalStatus.CONFLICTED,
    }
)


def is_retrievable_proposal_status(status: ProposalStatus | str) -> bool:
    value = ProposalStatus(status) if isinstance(status, str) else status
    return value in RETRIEVABLE_PROPOSAL_STATUSES


def is_excluded_proposal_status(status: ProposalStatus | str) -> bool:
    value = ProposalStatus(status) if isinstance(status, str) else status
    return value in EXCLUDED_PROPOSAL_STATUSES


def memory_truth_class_for_proposal(*, approved: bool) -> TruthClass:
    return TruthClass.APPROVED_DERIVED if approved else TruthClass.DERIVED_PROPOSAL


def is_active_memory_status(status: MemoryRevisionStatus | str) -> bool:
    value = MemoryRevisionStatus(status) if isinstance(status, str) else status
    return value == MemoryRevisionStatus.ACTIVE


def is_retracted_memory_status(status: MemoryRevisionStatus | str) -> bool:
    value = MemoryRevisionStatus(status) if isinstance(status, str) else status
    return value == MemoryRevisionStatus.RETRACTED
