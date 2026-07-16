"""Unit tests for learning eligibility, cycles, evidence replay, and FSRS."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from memdot_domain.evidence_twin import LearnerEventRecord, replay_evidence
from memdot_domain.fsrs import FsrsRating, initial_card, map_outcome_to_rating, schedule
from memdot_domain.learning import (
    EvidenceEligibility,
    EvidenceState,
    LearnerEventType,
    classify_event_eligibility,
    would_create_cycle,
)


def test_hint_and_reveal_are_ineligible() -> None:
    elig, reason = classify_event_eligibility(LearnerEventType.HINT_REVEALED)
    assert elig == EvidenceEligibility.INELIGIBLE
    assert reason == "hint_revealed"
    elig2, _ = classify_event_eligibility(
        LearnerEventType.GRADE_RECORDED, answer_revealed=True
    )
    assert elig2 == EvidenceEligibility.INELIGIBLE


def test_confirmed_prerequisite_cycle_detection() -> None:
    edges = [("a", "b"), ("b", "c")]
    assert would_create_cycle(edges, new_from="c", new_to="a") is True
    assert would_create_cycle(edges, new_from="a", new_to="d") is False


def test_evidence_replay_ignores_ineligible_and_duplicates() -> None:
    concept = uuid.uuid4()
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    e1 = uuid.uuid4()
    events = [
        LearnerEventRecord(
            event_id=e1,
            event_type=LearnerEventType.GRADE_RECORDED.value,
            concept_node_id=concept,
            assessment_item_id=uuid.uuid4(),
            occurred_at=t0 + timedelta(seconds=2),
            eligibility=EvidenceEligibility.ELIGIBLE.value,
            payload={"correct": True},
        ),
        # duplicate
        LearnerEventRecord(
            event_id=e1,
            event_type=LearnerEventType.GRADE_RECORDED.value,
            concept_node_id=concept,
            assessment_item_id=uuid.uuid4(),
            occurred_at=t0 + timedelta(seconds=2),
            eligibility=EvidenceEligibility.ELIGIBLE.value,
            payload={"correct": True},
        ),
        LearnerEventRecord(
            event_id=uuid.uuid4(),
            event_type=LearnerEventType.ANSWER_REVEALED.value,
            concept_node_id=concept,
            assessment_item_id=uuid.uuid4(),
            occurred_at=t0 + timedelta(seconds=1),
            eligibility=EvidenceEligibility.INELIGIBLE.value,
            payload={},
        ),
        LearnerEventRecord(
            event_id=uuid.uuid4(),
            event_type=LearnerEventType.GRADE_RECORDED.value,
            concept_node_id=concept,
            assessment_item_id=uuid.uuid4(),
            occurred_at=t0 + timedelta(seconds=3),
            eligibility=EvidenceEligibility.ELIGIBLE.value,
            payload={"correct": True},
        ),
    ]
    projected = replay_evidence(events)
    state = projected[concept]
    assert state.eligible_grades == 2
    assert state.evidence_state == EvidenceState.DELAYED_DEMONSTRATED
    assert state.ineligible_hits == 1


def test_fsrs_again_and_good_are_deterministic() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    card = initial_card(now=now)
    again = schedule(card, FsrsRating.AGAIN, now=now)
    good = schedule(card, FsrsRating.GOOD, now=now)
    assert again.lapses == 1
    assert again.due_at > now
    assert good.reps == 1
    assert good.stability > card.stability
    assert map_outcome_to_rating(correct=False) == FsrsRating.AGAIN
    assert map_outcome_to_rating(correct=True, revealed=True) == FsrsRating.AGAIN
    assert map_outcome_to_rating(correct=True) == FsrsRating.GOOD
