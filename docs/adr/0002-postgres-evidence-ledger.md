# ADR 0002: PostgreSQL Evidence Ledger

- Status: Accepted
- Date: 2026-07-15

## Context

Memdot needs one inspectable source of truth for knowledge, provenance, permissions, memory decisions, attempts, and learning evidence. Search indexes and model-specific memory stores cannot safely own canonical user state.

## Decision

- PostgreSQL is the canonical transactional store and **Evidence Ledger**.
- Immutable originals live in object storage; PostgreSQL stores their identity, ownership, hashes, versions, processing state, and provenance.
- Canonical tables cover accounts, Spaces, source versions, normalized documents, memory proposals and decisions, interactions, attempts, learning events, context receipts, grants, and deletion state.
- Evidence-producing changes append versioned events. Corrections use superseding or compensating records; mutable read models are projections of that history.
- Every evidence row records actor, event type, occurred/recorded time, Space, source/version references, schema version, and provenance quality.
- A transactional outbox drives Tex, embeddings, search, schedules, and integration jobs. Projection completion is never required for the canonical commit to succeed.
- Row-level tenancy and application authorization are both mandatory.

## Alternatives

- Make a vector or memory database canonical: rejected because authorization, transactions, corrections, and provenance become fragile.
- Use event sourcing for every product field: rejected as unnecessary operational complexity; only evidence-bearing history is append-oriented.
- Use a document database: rejected because the core model is relational and requires transactional constraints.

## Consequences

- Canonical writes remain explainable and recoverable even if derived systems fail.
- Projection consumers must be idempotent and tolerate replay and out-of-order delivery.
- Storage growth is managed through partitioning and retention policies, not destructive rewriting of evidence history.

## Security effect

Use encryption in transit and at rest, per-account/Space authorization, least-privilege database roles, audited administrative access, and field-level envelope encryption for secrets. Deletion must cascade through canonical records and publish tombstones to every projection.

## Reversal strategy

The ledger schema and outbox are exposed through repository interfaces. PostgreSQL can be partitioned, replicated, or migrated by replaying versioned exports without making any projection authoritative.

## Links

- [PostgreSQL documentation](https://www.postgresql.org/docs/)
- [ADR 0003: Tex as a replaceable projection](0003-tex-replaceable-projection.md)
- [ADR 0012: Evidence Twin, event ledger, and FSRS](0012-evidence-twin-event-ledger-and-fsrs.md)
