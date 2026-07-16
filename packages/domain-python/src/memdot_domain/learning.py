"""Learning curriculum, assessment, and eligibility helpers."""

from __future__ import annotations

from enum import StrEnum


class CurriculumNodeKind(StrEnum):
    UNIT = "unit"
    OBJECTIVE = "objective"
    CONCEPT = "concept"
    SOURCE_UNIT = "source_unit"


class ConfirmationState(StrEnum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"


class AssessmentItemType(StrEnum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    WRITTEN = "written"


class AssessmentState(StrEnum):
    DRAFT = "draft"
    PROVISIONAL = "provisional"
    HUMAN_VERIFIED = "human_verified"
    RETIRED = "retired"


class LearnerEventType(StrEnum):
    ATTEMPT_STARTED = "attempt_started"
    RESPONSE_CAPTURED = "response_captured"
    CONFIDENCE_RECORDED = "confidence_recorded"
    HINT_REQUESTED = "hint_requested"
    HINT_REVEALED = "hint_revealed"
    ANSWER_REVEALED = "answer_revealed"
    GRADE_RECORDED = "grade_recorded"
    REVIEW_RATED = "review_rated"
    ITEM_RETIRED = "item_retired"
    USER_CHAT_MARKER = "user_chat_marker"
    PROJECTION_CORRECTED = "projection_corrected"


class EvidenceEligibility(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


class EvidenceState(StrEnum):
    UNASSESSED = "unassessed"
    PRACTICING = "practicing"
    DEMONSTRATED = "demonstrated"
    DELAYED_DEMONSTRATED = "delayed_demonstrated"


class RecallState(StrEnum):
    CURRENT = "current"
    DUE = "due"
    LAPSED = "lapsed"


class ConfidenceLabel(StrEnum):
    GUESSING = "guessing"
    UNSURE = "unsure"
    SURE = "sure"


# Events that structurally cannot raise demonstrated mastery.
INELIGIBLE_MASTERY_EVENTS = frozenset(
    {
        LearnerEventType.HINT_REVEALED,
        LearnerEventType.ANSWER_REVEALED,
        LearnerEventType.USER_CHAT_MARKER,
    }
)


def classify_event_eligibility(
    event_type: LearnerEventType | str,
    *,
    answer_revealed: bool = False,
    substantive_hint: bool = False,
    response_before_feedback: bool = True,
) -> tuple[EvidenceEligibility, str | None]:
    et = LearnerEventType(event_type)
    if et in INELIGIBLE_MASTERY_EVENTS:
        return EvidenceEligibility.INELIGIBLE, et.value
    if answer_revealed:
        return EvidenceEligibility.INELIGIBLE, "answer_revealed"
    if substantive_hint:
        return EvidenceEligibility.INELIGIBLE, "substantive_hint"
    if not response_before_feedback and et == LearnerEventType.GRADE_RECORDED:
        return EvidenceEligibility.INELIGIBLE, "response_after_feedback"
    return EvidenceEligibility.ELIGIBLE, None


def would_create_cycle(
    edges: list[tuple[str, str]],
    *,
    new_from: str,
    new_to: str,
) -> bool:
    """Return True if adding confirmed edge new_from -> new_to creates a cycle."""
    graph: dict[str, set[str]] = {}
    for src, dst in edges:
        graph.setdefault(src, set()).add(dst)
    graph.setdefault(new_from, set()).add(new_to)

    visited: set[str] = set()
    stack: set[str] = set()

    def dfs(node: str) -> bool:
        if node in stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for nxt in graph.get(node, ()):
            if dfs(nxt):
                return True
        stack.remove(node)
        return False

    return dfs(new_from)
