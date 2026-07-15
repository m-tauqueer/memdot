# ADR 0004: Parser-Neutral Document Model

- Status: Accepted
- Date: 2026-07-15

## Context

Memdot will ingest PDFs, Markdown, office files, notes applications, web content, and future formats. Parser-specific output cannot be allowed to leak into retrieval, citations, editing, or sync contracts.

## Decision

- Preserve every imported original as an immutable, content-addressed source version.
- Parser adapters produce a versioned normalized document composed of ordered blocks with stable IDs, semantic type, text, hierarchy, table/math/media references, language, and source locators.
- Locators may include page, heading path, character range, bounding box, external block ID, and parser confidence. They must always point to a specific source version.
- Parser output, warnings, parser name/version, and checksums are recorded so the same source can be reprocessed and compared.
- Chunking and embeddings consume normalized blocks but remain separate, rebuildable projections.
- Unsupported content is represented as an explicit opaque block or warning, never silently dropped.
- Editing uses the MemdotDocument contract from ADR 0009; mapping between normalized import blocks and editable blocks preserves provenance.

## Alternatives

- Store only extracted plain text: rejected because it destroys structure and citation fidelity.
- Adopt one parser's JSON as canonical: rejected because it creates vendor lock-in and unstable migrations.
- Convert every import directly to editor JSON: rejected because parsing evidence and user-authored content have different lifecycles.

## Consequences

- New parsers can be evaluated without changing retrieval or UI contracts.
- Normalization and source-locator conformance require dedicated fixtures.
- Re-parsing creates a new derived version and never overwrites prior provenance.

## Security effect

Parsing runs in isolated workers with file-type, size, time, and decompression limits. Imported HTML and active content are sanitized. Originals and parser artifacts inherit account/Space access and deletion rules.

## Reversal strategy

Schema versions and migration adapters allow a new normalized model to run alongside the old one. Reprocess immutable originals, compare block/provenance coverage, then switch consumers.

## Links

- [ADR 0002: PostgreSQL Evidence Ledger](0002-postgres-evidence-ledger.md)
- [ADR 0009: Tiptap and MemdotDocument](0009-tiptap-and-memdotdocument.md)
