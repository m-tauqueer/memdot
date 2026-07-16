"""Learning domain service: curriculum, sealed assessments, events, scheduling."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from memdot_domain.evidence_twin import LearnerEventRecord, replay_evidence
from memdot_domain.fsrs import (
    FsrsCard,
    initial_card,
    map_outcome_to_rating,
    schedule,
    scheduling_priority,
)
from memdot_domain.ids import new_uuid7
from memdot_domain.learning import (
    AssessmentItemType,
    AssessmentState,
    ConfirmationState,
    CurriculumNodeKind,
    LearnerEventType,
    classify_event_eligibility,
    would_create_cycle,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import (
    AssessmentAttempt,
    AssessmentItem,
    AssessmentRevision,
    Course,
    CurriculumEdge,
    CurriculumNode,
    LearnerEvent,
    LearnerProjection,
    ReviewItem,
)
from memdot_core.db.tenant import tenant_scope
from memdot_core.request_context import RequestContext


@dataclass(frozen=True)
class CourseResult:
    course_id: uuid.UUID
    space_id: uuid.UUID


def create_course(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID,
    title: str,
) -> CourseResult:
    course_id = new_uuid7()
    with tenant_scope(db, ctx.tenant()):
        db.add(
            Course(
                id=course_id,
                account_id=ctx.account_id,
                space_id=space_id,
                title=title,
            )
        )
    return CourseResult(course_id=course_id, space_id=space_id)


def add_curriculum_node(
    db: Session,
    ctx: RequestContext,
    *,
    course_id: uuid.UUID,
    kind: str,
    title: str,
    confirmation: str = ConfirmationState.SUGGESTED.value,
) -> uuid.UUID:
    with tenant_scope(db, ctx.tenant()):
        course = db.execute(
            select(Course).where(Course.account_id == ctx.account_id, Course.id == course_id)
        ).scalar_one()
        node_id = new_uuid7()
        db.add(
            CurriculumNode(
                id=node_id,
                account_id=ctx.account_id,
                space_id=course.space_id,
                course_id=course_id,
                kind=CurriculumNodeKind(kind).value,
                title=title,
                confirmation=ConfirmationState(confirmation).value,
            )
        )
    return node_id


def add_prerequisite_edge(
    db: Session,
    ctx: RequestContext,
    *,
    course_id: uuid.UUID,
    from_node_id: uuid.UUID,
    to_node_id: uuid.UUID,
    confirmation: str = ConfirmationState.CONFIRMED.value,
) -> uuid.UUID:
    with tenant_scope(db, ctx.tenant()):
        course = db.execute(
            select(Course).where(Course.account_id == ctx.account_id, Course.id == course_id)
        ).scalar_one()
        existing = (
            db.execute(
                select(CurriculumEdge).where(
                    CurriculumEdge.account_id == ctx.account_id,
                    CurriculumEdge.course_id == course_id,
                    CurriculumEdge.confirmation == ConfirmationState.CONFIRMED.value,
                )
            )
            .scalars()
            .all()
        )
        edge_pairs = [(str(e.from_node_id), str(e.to_node_id)) for e in existing]
        if confirmation == ConfirmationState.CONFIRMED.value and would_create_cycle(
            edge_pairs, new_from=str(from_node_id), new_to=str(to_node_id)
        ):
            msg = "confirmed_prerequisite_cycle"
            raise ValueError(msg)
        edge_id = new_uuid7()
        db.add(
            CurriculumEdge(
                id=edge_id,
                account_id=ctx.account_id,
                space_id=course.space_id,
                course_id=course_id,
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                edge_kind="prerequisite",
                confirmation=ConfirmationState(confirmation).value,
            )
        )
    return edge_id


def create_assessment(
    db: Session,
    ctx: RequestContext,
    *,
    course_id: uuid.UUID,
    title: str,
    item_type: str,
    prompt: str,
    sealed_answer: dict[str, Any],
    concept_node_id: uuid.UUID | None = None,
    sealed_rubric: dict[str, Any] | None = None,
    source_locators: list[Any] | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    canonical = json.dumps(
        {"prompt": prompt, "answer": sealed_answer, "type": item_type},
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with tenant_scope(db, ctx.tenant()):
        course = db.execute(
            select(Course).where(Course.account_id == ctx.account_id, Course.id == course_id)
        ).scalar_one()
        item_id = new_uuid7()
        rev_id = new_uuid7()
        db.add(
            AssessmentItem(
                id=item_id,
                account_id=ctx.account_id,
                space_id=course.space_id,
                course_id=course_id,
                concept_node_id=concept_node_id,
                title=title,
            )
        )
        db.flush()
        db.add(
            AssessmentRevision(
                id=rev_id,
                account_id=ctx.account_id,
                space_id=course.space_id,
                assessment_item_id=item_id,
                item_type=AssessmentItemType(item_type).value,
                prompt=prompt,
                sealed_answer=sealed_answer,
                sealed_rubric=sealed_rubric or {},
                source_locators=source_locators or [],
                state=AssessmentState.PROVISIONAL.value,
                content_sha256=digest,
            )
        )
    return item_id, rev_id


def get_assessment_for_attempt(
    db: Session,
    ctx: RequestContext,
    *,
    assessment_item_id: uuid.UUID,
    revision_id: uuid.UUID,
) -> dict[str, Any]:
    """Return prompt-only payload; sealed answer/rubric are never included."""
    with tenant_scope(db, ctx.tenant()):
        rev = db.execute(
            select(AssessmentRevision).where(
                AssessmentRevision.account_id == ctx.account_id,
                AssessmentRevision.assessment_item_id == assessment_item_id,
                AssessmentRevision.id == revision_id,
            )
        ).scalar_one()
    return {
        "assessmentItemId": str(assessment_item_id),
        "revisionId": str(revision_id),
        "itemType": rev.item_type,
        "prompt": rev.prompt,
        "state": rev.state,
        # Explicitly omit sealed_answer and sealed_rubric.
    }


def start_assessment_attempt(
    db: Session,
    ctx: RequestContext,
    *,
    course_id: uuid.UUID,
    assessment_item_id: uuid.UUID,
    assessment_revision_id: uuid.UUID,
    client_attempt_id: str | None = None,
) -> dict[str, Any]:
    with tenant_scope(db, ctx.tenant()):
        course = db.execute(
            select(Course).where(Course.account_id == ctx.account_id, Course.id == course_id)
        ).scalar_one()
        item = db.execute(
            select(AssessmentItem).where(
                AssessmentItem.account_id == ctx.account_id,
                AssessmentItem.id == assessment_item_id,
                AssessmentItem.course_id == course_id,
                AssessmentItem.space_id == course.space_id,
            )
        ).scalar_one()
        db.execute(
            select(AssessmentRevision).where(
                AssessmentRevision.account_id == ctx.account_id,
                AssessmentRevision.id == assessment_revision_id,
                AssessmentRevision.assessment_item_id == item.id,
                AssessmentRevision.space_id == course.space_id,
            )
        ).scalar_one()
        if client_attempt_id:
            existing = db.execute(
                select(AssessmentAttempt).where(
                    AssessmentAttempt.account_id == ctx.account_id,
                    AssessmentAttempt.client_attempt_id == client_attempt_id,
                )
            ).scalar_one_or_none()
            if existing is not None:
                if (
                    existing.user_id != ctx.user_id
                    or existing.course_id != course_id
                    or existing.assessment_item_id != assessment_item_id
                    or existing.assessment_revision_id != assessment_revision_id
                ):
                    raise ValueError("idempotency_conflict")
                return {
                    "attemptId": str(existing.id),
                    "status": existing.status,
                    "idempotent": True,
                }
        attempt_id = new_uuid7()
        db.add(
            AssessmentAttempt(
                id=attempt_id,
                account_id=ctx.account_id,
                space_id=course.space_id,
                user_id=ctx.user_id,
                course_id=course_id,
                assessment_item_id=assessment_item_id,
                assessment_revision_id=assessment_revision_id,
                response_json={},
                status="in_progress",
                client_attempt_id=client_attempt_id,
            )
        )
        db.add(
            LearnerEvent(
                id=new_uuid7(),
                account_id=ctx.account_id,
                space_id=course.space_id,
                course_id=course_id,
                user_id=ctx.user_id,
                assessment_item_id=assessment_item_id,
                assessment_revision_id=assessment_revision_id,
                attempt_id=attempt_id,
                client_event_id=f"attempt-started:{attempt_id}",
                event_type=LearnerEventType.ATTEMPT_STARTED.value,
                occurred_at=datetime.now(UTC),
                payload={},
                eligibility="ineligible",
                exclusion_reason="attempt_started",
            )
        )
    return {"attemptId": str(attempt_id), "status": "in_progress", "idempotent": False}


def record_attempt_reveal(
    db: Session,
    ctx: RequestContext,
    *,
    attempt_id: uuid.UUID,
    hint: bool = False,
    answer: bool = False,
) -> dict[str, Any] | None:
    """Server records hint/answer reveal — clients cannot forge this at submit."""
    with tenant_scope(db, ctx.tenant()):
        row = db.execute(
            select(AssessmentAttempt).where(
                AssessmentAttempt.account_id == ctx.account_id,
                AssessmentAttempt.id == attempt_id,
                AssessmentAttempt.user_id == ctx.user_id,
            )
        ).scalar_one_or_none()
        if row is None or row.status != "in_progress":
            return None
        if hint:
            row.hint_revealed = True
            event_type = LearnerEventType.HINT_REVEALED.value
        else:
            event_type = LearnerEventType.ANSWER_REVEALED.value
        if answer:
            row.answer_revealed = True
            event_type = LearnerEventType.ANSWER_REVEALED.value
        if hint or answer:
            db.add(
                LearnerEvent(
                    id=new_uuid7(),
                    account_id=ctx.account_id,
                    space_id=row.space_id,
                    course_id=row.course_id,
                    user_id=ctx.user_id,
                    assessment_item_id=row.assessment_item_id,
                    assessment_revision_id=row.assessment_revision_id,
                    attempt_id=row.id,
                    client_event_id=f"{event_type}:{row.id}",
                    event_type=event_type,
                    occurred_at=datetime.now(UTC),
                    payload={},
                    eligibility="ineligible",
                    exclusion_reason=event_type,
                )
            )
        return {
            "attemptId": str(row.id),
            "hintRevealed": row.hint_revealed,
            "answerRevealed": row.answer_revealed,
            "status": row.status,
        }


def append_learner_event(
    db: Session,
    ctx: RequestContext,
    *,
    course_id: uuid.UUID,
    event_type: str,
    occurred_at: datetime,
    client_event_id: str | None = None,
    concept_node_id: uuid.UUID | None = None,
    assessment_item_id: uuid.UUID | None = None,
    assessment_revision_id: uuid.UUID | None = None,
    attempt_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    answer_revealed: bool = False,
    substantive_hint: bool = False,
    response_before_feedback: bool = True,
) -> uuid.UUID:
    """Append an event for the authenticated session user only (never client user_id)."""
    user_id = ctx.user_id
    body = payload or {}
    # Clients must not declare grade/correct/eligibility — strip adversarial keys.
    body = {
        key: value
        for key, value in body.items()
        if key not in {"correct", "grade", "eligibility", "eligible", "user_id"}
    }
    eligibility, reason = classify_event_eligibility(
        event_type,
        answer_revealed=answer_revealed,
        substantive_hint=substantive_hint,
        response_before_feedback=response_before_feedback,
    )
    with tenant_scope(db, ctx.tenant()):
        if client_event_id:
            existing = db.execute(
                select(LearnerEvent).where(
                    LearnerEvent.account_id == ctx.account_id,
                    LearnerEvent.client_event_id == client_event_id,
                )
            ).scalar_one_or_none()
            if existing is not None:
                return existing.id
        course = db.execute(
            select(Course).where(Course.account_id == ctx.account_id, Course.id == course_id)
        ).scalar_one()
        event_id = new_uuid7()
        db.add(
            LearnerEvent(
                id=event_id,
                account_id=ctx.account_id,
                space_id=course.space_id,
                course_id=course_id,
                user_id=user_id,
                concept_node_id=concept_node_id,
                assessment_item_id=assessment_item_id,
                assessment_revision_id=assessment_revision_id,
                attempt_id=attempt_id,
                client_event_id=client_event_id,
                event_type=LearnerEventType(event_type).value,
                occurred_at=occurred_at,
                payload=body,
                eligibility=eligibility.value,
                exclusion_reason=reason,
            )
        )
    return event_id


def submit_assessment_attempt(
    db: Session,
    ctx: RequestContext,
    *,
    course_id: uuid.UUID,
    assessment_item_id: uuid.UUID,
    assessment_revision_id: uuid.UUID,
    response: dict[str, Any],
    confidence: str | None,
    client_attempt_id: str | None = None,
    hint_revealed: bool = False,
    answer_revealed: bool = False,
) -> dict[str, Any]:
    """Server-grades from sealed answers; confidence must precede feedback."""
    if confidence is None or not str(confidence).strip():
        msg = "confidence_required_before_feedback"
        raise ValueError(msg)
    # Client reveal booleans are ignored; only server-recorded attempt state counts.
    _ = (hint_revealed, answer_revealed)
    if not client_attempt_id:
        raise ValueError("attempt_start_required")
    with tenant_scope(db, ctx.tenant()):
        existing = db.execute(
            select(AssessmentAttempt).where(
                AssessmentAttempt.account_id == ctx.account_id,
                AssessmentAttempt.user_id == ctx.user_id,
                AssessmentAttempt.client_attempt_id == client_attempt_id,
            )
        ).scalar_one_or_none()
        if existing is not None and existing.status == "graded":
            if (
                existing.course_id != course_id
                or existing.assessment_item_id != assessment_item_id
                or existing.assessment_revision_id != assessment_revision_id
            ):
                raise ValueError("idempotency_conflict")
            return {"attemptId": str(existing.id), "status": existing.status, "idempotent": True}
        course = db.execute(
            select(Course).where(Course.account_id == ctx.account_id, Course.id == course_id)
        ).scalar_one()
        rev = db.execute(
            select(AssessmentRevision).where(
                AssessmentRevision.account_id == ctx.account_id,
                AssessmentRevision.assessment_item_id == assessment_item_id,
                AssessmentRevision.id == assessment_revision_id,
            )
        ).scalar_one()
        sealed = dict(rev.sealed_answer or {})
        correct, grade_reason = grade_mcq(sealed, response)
        feedback_at = datetime.now(UTC)
        server_hint = False
        server_reveal = False
        attempt_id = new_uuid7()
        prior = db.execute(
            select(AssessmentAttempt).where(
                AssessmentAttempt.account_id == ctx.account_id,
                AssessmentAttempt.user_id == ctx.user_id,
                AssessmentAttempt.client_attempt_id == client_attempt_id,
                AssessmentAttempt.status == "in_progress",
            )
        ).scalar_one_or_none()
        if prior is not None:
            if (
                prior.course_id != course_id
                or prior.assessment_item_id != assessment_item_id
                or prior.assessment_revision_id != assessment_revision_id
            ):
                raise ValueError("attempt_target_mismatch")
            server_hint = bool(prior.hint_revealed)
            server_reveal = bool(prior.answer_revealed)
            prior.response_json = response
            prior.confidence = confidence
            prior.feedback_at = feedback_at
            prior.status = "graded"
            attempt_id = prior.id
        else:
            msg = "attempt_not_started"
            raise ValueError(msg)
        event_type = LearnerEventType.GRADE_RECORDED.value
        eligibility, reason = classify_event_eligibility(
            event_type,
            answer_revealed=server_reveal,
            substantive_hint=server_hint,
            response_before_feedback=True,
        )
        event_id = new_uuid7()
        db.add(
            LearnerEvent(
                id=event_id,
                account_id=ctx.account_id,
                space_id=course.space_id,
                course_id=course_id,
                user_id=ctx.user_id,
                assessment_item_id=assessment_item_id,
                assessment_revision_id=assessment_revision_id,
                attempt_id=attempt_id,
                client_event_id=f"attempt:{attempt_id}",
                event_type=event_type,
                occurred_at=feedback_at,
                payload={
                    "correct": correct,
                    "gradeReason": grade_reason,
                    "confidence": confidence,
                },
                eligibility=eligibility.value,
                exclusion_reason=reason,
            )
        )
    # FSRS only from eligible review events.
    if eligibility.value == "eligible":
        apply_review_rating(
            db,
            ctx,
            course_id=course_id,
            assessment_item_id=assessment_item_id,
            assessment_revision_id=assessment_revision_id,
            correct=correct,
            revealed=server_reveal,
            substantive_hint=server_hint,
        )
    return {
        "attemptId": str(attempt_id),
        "eventId": str(event_id),
        "correct": correct,
        "status": "graded",
        "eligibility": eligibility.value,
        "idempotent": False,
    }


def rebuild_evidence_projections(
    db: Session,
    ctx: RequestContext,
    *,
    course_id: uuid.UUID,
) -> dict[str, Any]:
    user_id = ctx.user_id
    with tenant_scope(db, ctx.tenant()):
        course = db.execute(
            select(Course).where(Course.account_id == ctx.account_id, Course.id == course_id)
        ).scalar_one()
        events = (
            db.execute(
                select(LearnerEvent).where(
                    LearnerEvent.account_id == ctx.account_id,
                    LearnerEvent.course_id == course_id,
                    LearnerEvent.user_id == user_id,
                )
            )
            .scalars()
            .all()
        )
        records = [
            LearnerEventRecord(
                event_id=e.id,
                event_type=e.event_type,
                concept_node_id=e.concept_node_id,
                assessment_item_id=e.assessment_item_id,
                occurred_at=e.occurred_at,
                eligibility=e.eligibility,
                payload=dict(e.payload or {}),
            )
            for e in events
        ]
        projected = replay_evidence(records)
        for concept_id, evidence in projected.items():
            row = db.execute(
                select(LearnerProjection).where(
                    LearnerProjection.account_id == ctx.account_id,
                    LearnerProjection.user_id == user_id,
                    LearnerProjection.concept_node_id == concept_id,
                )
            ).scalar_one_or_none()
            payload: dict[str, object] = {
                "eligible_grades": evidence.eligible_grades,
                "ineligible_hits": evidence.ineligible_hits,
            }
            if row is None:
                db.add(
                    LearnerProjection(
                        id=new_uuid7(),
                        account_id=ctx.account_id,
                        space_id=course.space_id,
                        course_id=course_id,
                        user_id=user_id,
                        concept_node_id=concept_id,
                        evidence_state=evidence.evidence_state.value,
                        recall_state=evidence.recall_state.value,
                        coverage=float(evidence.eligible_grades),
                        projection_json=payload,
                    )
                )
            else:
                row.evidence_state = evidence.evidence_state.value
                row.recall_state = evidence.recall_state.value
                row.coverage = float(evidence.eligible_grades)
                row.projection_json = payload
                row.updated_at = datetime.now(UTC)
    return {
        str(cid): {
            "evidenceState": ev.evidence_state.value,
            "recallState": ev.recall_state.value,
            "eligibleGrades": ev.eligible_grades,
            "ineligibleHits": ev.ineligible_hits,
        }
        for cid, ev in projected.items()
    }


def apply_review_rating(
    db: Session,
    ctx: RequestContext,
    *,
    course_id: uuid.UUID,
    assessment_item_id: uuid.UUID,
    assessment_revision_id: uuid.UUID,
    correct: bool,
    revealed: bool = False,
    substantive_hint: bool = False,
) -> dict[str, Any]:
    """Apply FSRS from server-derived outcomes for the session user only."""
    user_id = ctx.user_id
    rating = map_outcome_to_rating(
        correct=correct, revealed=revealed, substantive_hint=substantive_hint
    )
    with tenant_scope(db, ctx.tenant()):
        course = db.execute(
            select(Course).where(Course.account_id == ctx.account_id, Course.id == course_id)
        ).scalar_one()
        row = db.execute(
            select(ReviewItem).where(
                ReviewItem.account_id == ctx.account_id,
                ReviewItem.user_id == user_id,
                ReviewItem.assessment_item_id == assessment_item_id,
            )
        ).scalar_one_or_none()
        if row is None:
            card = initial_card()
            row = ReviewItem(
                id=new_uuid7(),
                account_id=ctx.account_id,
                space_id=course.space_id,
                course_id=course_id,
                user_id=user_id,
                assessment_item_id=assessment_item_id,
                assessment_revision_id=assessment_revision_id,
                fsrs_state={
                    "stability": card.stability,
                    "difficulty": card.difficulty,
                    "reps": card.reps,
                    "lapses": card.lapses,
                },
                due_at=card.due_at,
            )
            db.add(row)
            db.flush()
        else:
            state = dict(row.fsrs_state or {})
            card = FsrsCard(
                stability=float(str(state.get("stability", 1.0))),
                difficulty=float(str(state.get("difficulty", 5.0))),
                reps=int(str(state.get("reps", 0))),
                lapses=int(str(state.get("lapses", 0))),
                due_at=row.due_at or datetime.now(UTC),
            )
        updated = schedule(card, rating)
        row.fsrs_state = {
            "stability": updated.stability,
            "difficulty": updated.difficulty,
            "reps": updated.reps,
            "lapses": updated.lapses,
        }
        row.due_at = updated.due_at
        row.assessment_revision_id = assessment_revision_id
        row.priority = scheduling_priority(
            recall_state="lapsed" if rating.value == "again" else "due",
            due_at=updated.due_at,
            is_prerequisite=False,
            pinned=False,
        )
        row.updated_at = datetime.now(UTC)
    return {
        "rating": rating.value,
        "dueAt": updated.due_at.isoformat(),
        "stability": updated.stability,
        "difficulty": updated.difficulty,
        "priority": row.priority,
    }


def grade_mcq(
    sealed_answer: dict[str, Any],
    response: dict[str, Any],
) -> tuple[bool, str]:
    expected = sealed_answer.get("correctOption")
    actual = response.get("selectedOption")
    if expected is None or actual is None:
        return False, "ungradable"
    return str(expected) == str(actual), "deterministic_rule"
