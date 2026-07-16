"""Deterministic Evidence Twin projection from eligible learner events."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from memdot_domain.learning import (
    EvidenceEligibility,
    EvidenceState,
    LearnerEventType,
    RecallState,
)


@dataclass(frozen=True)
class LearnerEventRecord:
    event_id: uuid.UUID
    event_type: str
    concept_node_id: uuid.UUID | None
    assessment_item_id: uuid.UUID | None
    occurred_at: datetime
    eligibility: str
    payload: dict[str, object] = field(default_factory=lambda: {})


@dataclass
class ConceptEvidence:
    concept_node_id: uuid.UUID
    evidence_state: EvidenceState = EvidenceState.UNASSESSED
    recall_state: RecallState = RecallState.CURRENT
    eligible_grades: int = 0
    ineligible_hits: int = 0


def replay_evidence(
    events: list[LearnerEventRecord],
) -> dict[uuid.UUID, ConceptEvidence]:
    """Replay events deterministically under duplicates and reordering."""
    # Stable order: occurred_at then event_id. Deduplicate by event_id.
    seen: set[uuid.UUID] = set()
    ordered = sorted(events, key=lambda e: (e.occurred_at, str(e.event_id)))
    projections: dict[uuid.UUID, ConceptEvidence] = {}

    for event in ordered:
        if event.event_id in seen:
            continue
        seen.add(event.event_id)
        if event.concept_node_id is None:
            continue
        state = projections.setdefault(
            event.concept_node_id, ConceptEvidence(concept_node_id=event.concept_node_id)
        )
        if event.eligibility != EvidenceEligibility.ELIGIBLE.value:
            state.ineligible_hits += 1
            # Ineligible activity never raises demonstrated mastery.
            if state.evidence_state == EvidenceState.UNASSESSED:
                state.evidence_state = EvidenceState.PRACTICING
            continue

        et = event.event_type
        if et == LearnerEventType.ATTEMPT_STARTED.value:
            if state.evidence_state == EvidenceState.UNASSESSED:
                state.evidence_state = EvidenceState.PRACTICING
        elif et == LearnerEventType.GRADE_RECORDED.value:
            correct = bool(event.payload.get("correct", False))
            if correct:
                state.eligible_grades += 1
                if state.eligible_grades >= 2:
                    state.evidence_state = EvidenceState.DELAYED_DEMONSTRATED
                else:
                    state.evidence_state = EvidenceState.DEMONSTRATED
                state.recall_state = RecallState.CURRENT
            else:
                state.evidence_state = EvidenceState.PRACTICING
                state.recall_state = RecallState.LAPSED
        elif et == LearnerEventType.REVIEW_RATED.value:
            rating = str(event.payload.get("rating", "again")).lower()
            if rating == "again":
                state.recall_state = RecallState.LAPSED
            elif rating in {"hard", "good", "easy"}:
                state.recall_state = RecallState.CURRENT
    return projections
