# ADR 0008: Proposed Writes and Best-Effort Interaction Capture

- Status: Accepted
- Date: 2026-07-15

## Context

External agents can discover useful memories and corrections, but direct writes would let an untrusted or mistaken model silently alter the user's long-term context. A host can explicitly send conversation turns to Memdot, but MCP does not passively reveal the host's complete conversation.

## Decision

- External agent writes create typed, idempotent **proposals**. They never directly commit canonical memories, source edits, or mastery changes.
- A proposal includes a non-private target Space, proposed statement/change, evidence references, originating client and interaction, confidence, schema version, and idempotency key.
- Users can accept, edit, reject, or leave a proposal pending. Acceptance creates a canonical versioned write and outbox event; rejection is retained only long enough to prevent repeated spam and support user controls.
- `record_interaction`, protected by its separate MCP write scope, stores in a non-private Space the raw user/assistant/tool message turns that the client explicitly supplies, plus client, timestamps, related receipts/IDs, and a client-declared completeness marker.
- Supplied raw turns are retained as canonical interaction history until the user deletes the interaction, chat, Space, or account. Calls are idempotent and support ordered append without overwriting prior turns.
- Capture is **best effort** because Memdot cannot passively observe host conversations. Missing calls or omitted turns remain missing, and the UI always exposes the source client and completeness marker rather than claiming a full transcript.
- Native Memdot tutoring may store its own transcript under the user's retention settings, but memory extraction still produces reviewable proposals.
- Recorded interactions never create or modify learning evidence, attempts, mastery, misconceptions, or FSRS state automatically. A separate qualifying product action is required.

## Alternatives

- Allow agents to write memory directly: rejected because poisoning and accidental persistence would be difficult to detect.
- Attempt passive or automatic host-transcript capture: rejected because MCP does not expose a reliable complete stream.
- Reduce recorded interactions to summaries only: rejected because explicitly supplied raw turns are needed for faithful future context and user inspection.
- Make external interactions read-only: rejected because useful corrections would be lost.

## Consequences

- The review inbox is a core workflow and needs batching, deduplication, and clear provenance.
- Interaction history can be rich when a client cooperates, but completeness varies visibly by host.
- Raw interaction retention increases storage and deletion responsibilities while preventing ungrounded learning-state changes.

## Security effect

Proposal and interaction text are untrusted input and are sanitized, size-limited, and scanned for unsafe active content before storage or review. Client revocation stops new records, and MCP writes are rejected if the target Space is Private. Raw turns are encrypted and access-controlled, are eligible for whole-account MCP read while their Space remains non-private, and are deleted on the user's request. Credentials are always stripped.

## Reversal strategy

Low-risk proposal types may later support user-configured auto-accept policies. The proposal ledger remains the audit boundary, so direct commit can be introduced narrowly without migrating existing data.

## Links

- [ADR 0002: PostgreSQL Evidence Ledger](0002-postgres-evidence-ledger.md)
- [ADR 0006: Context Compiler and receipts](0006-context-compiler-and-receipts.md)
- [ADR 0007: Whole-account MCP and private Spaces](0007-whole-account-mcp-and-private-spaces.md)
