# ADR 0003: Tex as a Replaceable Projection

- Status: Accepted
- Date: 2026-07-15

## Context

Tex can provide high-quality memory and retrieval behavior, but coupling canonical knowledge to one memory engine would make user data, deletion, self-hosting, and future experimentation dependent on its implementation.

## Decision

- Tex is a derived memory/retrieval projection behind a versioned `MemoryProjection` adapter.
- PostgreSQL and immutable source objects remain canonical. Tex stores only the indexed representations and metadata required for its jobs.
- Canonical commits emit outbox events; an idempotent worker applies them to Tex and records projection checkpoints and errors.
- Every Tex record carries account, Space, canonical object/version, visibility, and deletion identifiers.
- Retrieval results must resolve back to canonical evidence before the Context Compiler can use them.
- Tex can be rebuilt from canonical source versions, accepted memories, and learning evidence. Rebuild and integrity-check commands are required before production use.
- If Tex is unavailable, Memdot falls back to PostgreSQL exact and version lookup, graph traversal, and pgvector search using local embeddings and a local reranker. Projection work is queued and canonical writes continue.

## Alternatives

- Make Tex the source of truth: rejected because transactions, provenance, portability, and erasure would depend on it.
- Avoid Tex and build all memory behavior directly in PostgreSQL: rejected because it prevents using Tex's specialized capabilities and independent evolution.
- Dual-write from request handlers: rejected because partial failures create silent divergence.

## Consequences

- Tex can evolve quickly without owning product contracts.
- The platform must operate an outbox, replay tooling, lag monitoring, and reconciliation.
- Projection-specific ranking scores are hints, not canonical facts.

## Security effect

Tex receives only fields needed for retrieval, uses the same tenant/Space boundary, and is never reachable directly by clients. Revocation and deletion tombstones have priority over ordinary indexing work. Logs must not contain memory text.

## Reversal strategy

Implement a second projection adapter, replay canonical data into it, compare shadow results, then switch reads by configuration. No canonical-data migration is required.

## Links

- [Tex documentation](https://metacognition-fdc534de.mintlify.app/introduction)
- [pgvector](https://github.com/pgvector/pgvector)
- [ADR 0002: PostgreSQL Evidence Ledger](0002-postgres-evidence-ledger.md)
- [ADR 0005: Hybrid retrieval](0005-hybrid-retrieval.md)
