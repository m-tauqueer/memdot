"""Minimal deterministic FSRS-like scheduling helpers for review items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class FsrsRating(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


@dataclass(frozen=True)
class FsrsCard:
    stability: float
    difficulty: float
    reps: int
    lapses: int
    due_at: datetime
    last_review_at: datetime | None = None


DEFAULT_RETENTION = 0.90


def initial_card(*, now: datetime | None = None) -> FsrsCard:
    ts = now or datetime.now(UTC)
    return FsrsCard(
        stability=1.0,
        difficulty=5.0,
        reps=0,
        lapses=0,
        due_at=ts,
        last_review_at=None,
    )


def map_outcome_to_rating(
    *,
    correct: bool,
    revealed: bool = False,
    substantive_hint: bool = False,
    scaffold: bool = False,
    effortless: bool = False,
) -> FsrsRating:
    if not correct or revealed or substantive_hint:
        return FsrsRating.AGAIN
    if scaffold:
        return FsrsRating.HARD
    if effortless:
        return FsrsRating.EASY
    return FsrsRating.GOOD


def schedule(
    card: FsrsCard,
    rating: FsrsRating | str,
    *,
    now: datetime | None = None,
) -> FsrsCard:
    """Deterministic interval update (simplified FSRS-compatible mapping)."""
    ts = now or datetime.now(UTC)
    r = FsrsRating(rating)
    stability = card.stability
    difficulty = card.difficulty
    reps = card.reps
    lapses = card.lapses

    if r == FsrsRating.AGAIN:
        stability = max(0.5, stability * 0.5)
        difficulty = min(10.0, difficulty + 1.0)
        lapses += 1
        reps = 0
        due = ts + timedelta(minutes=10)
    elif r == FsrsRating.HARD:
        stability = max(1.0, stability * 1.2)
        difficulty = min(10.0, difficulty + 0.5)
        reps += 1
        due = ts + timedelta(days=max(1.0, stability * 0.8))
    elif r == FsrsRating.GOOD:
        stability = max(1.0, stability * 1.8)
        reps += 1
        due = ts + timedelta(days=max(1.0, stability))
    else:  # EASY
        stability = max(1.0, stability * 2.4)
        difficulty = max(1.0, difficulty - 0.5)
        reps += 1
        due = ts + timedelta(days=max(2.0, stability * 1.3))

    return FsrsCard(
        stability=round(stability, 4),
        difficulty=round(difficulty, 4),
        reps=reps,
        lapses=lapses,
        due_at=due,
        last_review_at=ts,
    )


def scheduling_priority(
    *,
    recall_state: str,
    due_at: datetime | None,
    is_prerequisite: bool,
    pinned: bool,
    now: datetime | None = None,
) -> int:
    """Lower number = higher priority (TRD-LRN-010 ordering)."""
    ts = now or datetime.now(UTC)
    if recall_state == "lapsed" and is_prerequisite:
        return 0
    if recall_state == "due" and is_prerequisite:
        return 1
    if due_at is not None and due_at <= ts:
        return 2
    if pinned:
        return 4
    return 3
