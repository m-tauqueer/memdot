# ADR 0009: Tiptap and MemdotDocument

- Status: Accepted
- Date: 2026-07-15

## Context

Memdot needs a rich, collaborative-ready editor for notes and normalized imports without making persisted content dependent on a UI library's undocumented internals or on unsafe HTML.

## Decision

- Tiptap is the web editor toolkit.
- The persistence and interchange contract is a versioned **MemdotDocument** JSON schema based on an allowlisted ProseMirror-compatible tree, not raw HTML.
- MemdotDocument defines supported nodes and marks, stable block IDs, document metadata, schema version, source/provenance links, and extension data under namespaced fields.
- Documents are validated on every write. Migrations are explicit, deterministic, and preserve unknown namespaced data where safe.
- Imported normalized blocks map into MemdotDocument without erasing their source/version locators. User edits create a new authored version rather than mutating the imported source evidence.
- Markdown and sanitized HTML are export/render formats, not canonical storage. Tiptap-specific commands and UI state are not persisted as domain data.
- Collaborative editing is deferred, but stable IDs and version preconditions keep that path open.

## Alternatives

- Store HTML: rejected because validation, migrations, semantic blocks, and safe rendering are weak.
- Persist unrestricted Tiptap JSON: rejected because plugin changes would silently change the product schema.
- Build a custom editor: rejected because editor mechanics are not Memdot's differentiator.

## Consequences

- Every editor extension requires a schema and migration review.
- Server-side rendering, ingestion, search, and export share a stable document contract.
- Some Tiptap extensions cannot be enabled until their data representation is accepted.

## Security effect

Renderers escape text and sanitize links/embeds. Active HTML and executable embeds are prohibited. Document authorization uses account and Space ownership independently of editor state; collaborative cursors, if added, must be ephemeral.

## Reversal strategy

Because MemdotDocument is library-neutral domain JSON, a different ProseMirror UI or editor can be introduced through an adapter. Schema migrations can be shadow-run and reversed using prior immutable versions.

## Links

- [Tiptap documentation](https://tiptap.dev/docs)
- [ProseMirror guide](https://prosemirror.net/docs/guide/)
- [ADR 0004: Parser-neutral document model](0004-parser-neutral-document-model.md)
