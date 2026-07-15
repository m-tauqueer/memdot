# ADR 0007: Whole-Account MCP and Private Spaces

- Status: Accepted
- Date: 2026-07-15

## Context

Users want Gemini, Claude, ChatGPT, and other agents to use their complete eligible Memdot memory without creating and maintaining a separate server or grant for every course. Users also need a categorical Space boundary that external AI can never cross.

## Decision

- Memdot exposes one MCP endpoint per account deployment. Each external client uses OAuth with a named, revocable grant, short-lived access tokens, and rotating refresh tokens.
- V1 has one read scope: `memdot.memory.read`. It is a fixed whole-account grant covering sources, approved memory, learner summaries, completed attempts, and retained chats across every current and future non-private Space.
- V1 offers no per-Space or per-data-class selection for that read scope. A user either grants the whole eligible account memory or does not connect the client.
- Spaces explicitly marked Private are categorically excluded from MCP reads and write targets. Sealed answer keys, secrets, pending/unapproved memory, incomplete attempts, and other content carrying an external-AI exclusion are also never returned.
- Tool responses are bounded, purpose-specific evidence bundles from the Context Compiler, not unrestricted database or document dumps.
- Writes are separate grants: `memdot.memory.propose` permits typed memory proposals, and `memdot.interaction.record` permits explicit calls to `record_interaction`. Neither scope permits canonical memory commits or automatic learner-evidence changes.
- Users can inspect each connection, its read/write grants, captured interactions, and context receipts, and can revoke it immediately.
- No public links, anonymous MCP, shared API keys, or cross-account search are introduced by account-wide access.

## Alternatives

- Run one MCP server or credential per Space: rejected because setup and revocation do not scale for normal users.
- Offer per-Space or per-data-class read checkboxes: rejected in V1 because the product contract is one comprehensible whole-memory grant with a categorical Private-Space escape hatch.
- Give a connected agent raw database access: rejected because bounded context, sealed content, and provenance still require enforcement.
- Publish documents as URLs for agents: rejected because public exposure is incompatible with the account boundary.

## Consequences

- A single read grant can answer cross-course questions without repeated consent prompts.
- Users who do not want any content from a Space to reach external AI must mark it Private before invoking an external-AI action; changing the flag cannot claw back content already returned to a provider.
- Grant UX, Space-category transitions, sealed-content filters, and server-side scope tests are critical product infrastructure.
- External clients may not support every scope or receipt affordance; the server remains authoritative.

## Security effect

The consent screen names every included data class and states that all current and future non-private Spaces are covered. It also explains that returned content leaves Memdot and cannot be clawed back from the external AI. Token, client, user, account, Space category, sealed-content state, and scope are checked on every read and write. Tool arguments and results are not placed in operational logs.

## Reversal strategy

Additional grant models would require a new ADR because they change the V1 consent contract. The endpoint and canonical identifiers allow future institutional policies or narrower grants to be introduced under a new policy version; existing grants can be invalidated and re-consented.

## Links

- [Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-06-18)
- [ADR 0001: Spaces and Learning](0001-spaces-and-learning.md)
- [ADR 0006: Context Compiler and receipts](0006-context-compiler-and-receipts.md)
- [ADR 0008: Proposed writes and best-effort interaction capture](0008-proposed-writes-and-best-effort-interaction-capture.md)
