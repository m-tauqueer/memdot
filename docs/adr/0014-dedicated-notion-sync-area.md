# ADR 0014: Dedicated Notion Sync Area

- Status: Accepted
- Date: 2026-07-15

## Context

Many target users already organize class notes in Notion. A one-time generic import does not communicate connection scope, sync freshness, upstream deletions, or failures well enough for a continuing source.

## Decision

- Notion has a dedicated area in Integrations for connection, root setup, Space mapping, source selection, sync status, conflicts, errors, and disconnection.
- Each connection creates or designates one dedicated **Memdot root** in Notion. This root is the only subtree where Memdot may write.
- Selected Notion pages and databases outside the Memdot root sync inbound as read-only sources. Memdot never writes to, reparents, or deletes those external source pages.
- A user may explicitly approve a Memdot-authored document for Notion sync. Memdot creates it beneath the dedicated root; subsequent edits beneath that root sync in both directions.
- Only approved Memdot-authored documents participate in outbound sync. Imported sources, approved memories, learner evidence, attempts, chats, and system documents are never written to Notion implicitly.
- Stable Notion object IDs, Memdot document/version IDs, parent relationships, base revision/hash, `last_edited_time`, content hashes, and cursor/checkpoint state support idempotent incremental sync.
- Every sync creates immutable source/document versions and maps through the parser-neutral document model and MemdotDocument schema; Notion blocks are not canonical.
- Concurrent changes produce an explicit conflict with both versions available for user resolution. Sync pauses for that document and never uses silent last-write-wins.
- Moving a managed page outside the root, upstream deletion/archive, and local deletion are surfaced as explicit detach/delete conflicts; none silently cascade to accepted memory or learning evidence.
- Disconnecting revokes credentials and stops jobs. The user separately chooses whether imported sources and Memdot-authored synced documents are retained or deleted.
- Webhooks may accelerate discovery, but periodic reconciliation remains authoritative because events can be delayed or missed.

## Alternatives

- Treat Notion as a generic file upload: rejected because ongoing sync and permissions would be invisible.
- Make all selected Notion pages two-way: rejected because source pages outside the dedicated root must remain read-only.
- Keep all Notion sync one-way: rejected because users need approved Memdot-authored documents to remain editable under the dedicated root.
- Resolve concurrent edits with last-write-wins: rejected because it can silently destroy work and provenance.
- Make Notion blocks canonical Memdot documents: rejected because it couples the document model to one integration.

## Consequences

- Notion gets product-specific UX and operational monitoring before a generic connector framework is generalized.
- API limits, moved pages, revoked access, partial databases, and explicit conflicts require visible states and retries.
- The dedicated root makes outbound authority understandable but prevents arbitrary round-trip editing elsewhere in a workspace.
- Other integrations can reuse the source-version/checkpoint contracts without copying the Notion UI.

## Security effect

OAuth tokens are envelope-encrypted and never logged. Sync workers recheck connection, root ancestry, document approval, and Space ownership before every write; they minimize imported metadata, respect revocation, and sanitize rich content. The UI shows exactly which external pages are inbound-only and which root documents are two-way.

## Reversal strategy

The Notion adapter can move behind a generalized sync framework while preserving connection IDs, root ID, external object IDs, base revisions, conflicts, checkpoints, and source versions. Outbound sync can be disabled without changing inbound source history; expanding writes beyond the dedicated root requires a new ADR.

## Links

- [Notion API introduction](https://developers.notion.com/reference/intro)
- [Notion authorization](https://developers.notion.com/docs/authorization)
- [ADR 0001: Spaces and Learning](0001-spaces-and-learning.md)
- [ADR 0004: Parser-neutral document model](0004-parser-neutral-document-model.md)
