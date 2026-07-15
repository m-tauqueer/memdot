# ADR 0005: Hybrid Retrieval

- Status: Accepted
- Date: 2026-07-15

## Context

Student questions may depend on exact terms, semantic similarity, document structure, course relationships, recency, and personal learning evidence. Vector-only retrieval is neither reliable enough nor sufficiently explainable.

## Decision

- Retrieval is a staged, permission-aware pipeline: scope filtering, query planning, lexical search, vector search, structured/evidence lookup, fusion, reranking, diversification, and canonical evidence resolution.
- Native and internal callers can request the active Space, a permitted Space set, or an account-wide scope for their product purpose.
- MCP `memdot.memory.read` always searches the whole account across every non-private Space. It has no per-Space narrowing or expansion in V1, and Private Spaces are excluded before candidate generation.
- Lexical and vector indexes are replaceable projections. Course structure, accepted memories, and learning evidence are read through canonical identifiers.
- Rank fusion combines independently calibrated candidates; reranking cannot introduce evidence that was not retrieved and authorized.
- Results are evidence units containing canonical source/version, locator, relevant excerpt, retrieval reasons, freshness, and confidence—not anonymous text chunks.
- The pipeline returns explicit insufficiency when evidence is weak or contradictory. The model must not fill missing source context from an unlabelled guess.
- Evaluation uses a versioned benchmark covering exact lookup, conceptual questions, conflicting revisions, citations, authorization, and abstention.

## Alternatives

- Vector search only: rejected because exact names, version conflicts, and citations perform poorly.
- Send entire Spaces to the model: rejected because of cost, privacy, context limits, and low signal.
- Let each AI provider perform retrieval: rejected because behavior, residency, provenance, and portability would be provider-dependent.

## Consequences

- Retrieval is more operationally involved but independently testable.
- Index and reranker changes can be evaluated without changing canonical storage.
- Evidence resolution adds latency; caching may optimize only within identical authorization and version scopes.

## Security effect

Authorization and Space-category filters are applied before candidate generation and rechecked during canonical resolution. MCP cache keys include account, the effective set of current non-private Spaces, policy version, and source versions; native cache keys include their narrower scope. Retrieval logs store identifiers and metrics, not query or source content by default.

## Reversal strategy

Each stage is configured behind a versioned interface. Components can be shadowed, benchmarked, disabled, or replaced while preserving the evidence-unit output contract.

## Links

- [ADR 0003: Tex as a replaceable projection](0003-tex-replaceable-projection.md)
- [ADR 0006: Context Compiler and receipts](0006-context-compiler-and-receipts.md)
