# ADR 0012: Evidence Twin, Event Ledger, and FSRS

- Status: Accepted
- Date: 2026-07-15

## Context

Memdot must help a learner decide what to study next without hiding an opaque “mastery score” behind AI output. Knowledge state changes over time and must remain traceable to attempts, reviews, hints, corrections, and source revisions.

## Decision

- Each learner has an **Evidence Twin**: an inspectable projection of what the system has evidence they can recall, explain, or apply, including uncertainty and misconceptions.
- The twin is computed from the PostgreSQL learning-event ledger. Qualifying events include exposure, attempt, answer, hint, grading/rubric result, correction, self-rating, and review outcome.
- Events are append-only and reference account, Space, learning item/concept, source version, interaction/attempt, actor, timestamp, result, confidence, and evaluator/model version. Corrections supersede rather than erase prior interpretation.
- Learning items and concept links are versioned. LLMs may propose mappings and evaluations, but accepted evidence records the rubric and supporting artifacts.
- FSRS is the scheduling engine for reviewable items. Its state—difficulty, stability, due date, review history, and algorithm parameters—is stored as a rebuildable projection.
- Mastery/evidence confidence and FSRS retrievability are separate: one explains demonstrated capability; the other schedules likely forgetting.
- The Learning surface shows due work, evidence, uncertainty, and “why this is recommended.” Users can correct or remove inferred mappings.
- MCP `memdot.memory.read` may retrieve eligible completed attempts, retained raw chats, and the learner summary from every non-private Space as part of its fixed whole-account contract. Incomplete attempts, sealed answer keys, and Private-Space content remain excluded.
- Algorithm and evaluator versions are recorded so the twin and schedule can be recomputed.

## Alternatives

- A single LLM-generated mastery score: rejected because it is unstable and unexplainable.
- FSRS as the complete learner model: rejected because recall scheduling does not represent reasoning, transfer, or evidence quality.
- Overwrite learner state after every session: rejected because corrections and provenance would be lost.

## Consequences

- Event quality and concept identity matter more than decorative analytics.
- Recomputing projections is possible but requires versioned evaluator and scheduler parameters.
- Early evidence may remain uncertain instead of presenting false precision.

## Security effect

The Evidence Twin is inferred personal educational data. It is account-private, exportable, correctable, and deletable; it is not used for advertising or consequential eligibility decisions. The whole-account MCP consent explicitly names learner summaries, eligible completed attempts, and retained chats. Sealed answer keys, external-AI-excluded records, and all Private-Space data are filtered before retrieval.

## Reversal strategy

A replacement scheduler or evidence model can replay the versioned event ledger into a shadow projection and compare recommendations. Canonical attempt and event records remain unchanged.

## Links

- [FSRS project](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler)
- [ADR 0002: PostgreSQL Evidence Ledger](0002-postgres-evidence-ledger.md)
- [ADR 0007: Whole-account MCP and private Spaces](0007-whole-account-mcp-and-private-spaces.md)
- [ADR 0008: Proposed writes and best-effort interaction capture](0008-proposed-writes-and-best-effort-interaction-capture.md)
