# ADR 0001: Spaces and Learning

- Status: Accepted
- Date: 2026-07-15

## Context

Memdot must organize notes, syllabi, documents, imports, conversations, and learner evidence without becoming a generic folder tree. Knowledge ownership and the learning workflow are related but not the same concern.

## Decision

- A **Space** is the primary knowledge and organization boundary. A user creates one for a course, subject, project, or other durable context.
- Sources, documents, memories, conversations, and course structure belong to exactly one Space. Cross-Space references are explicit links, not implicit duplication.
- **Learning** is a first-class account-level surface. It shows reviews, attempts, progress, misconceptions, and due work across Spaces, with filters back to the originating Space.
- Learning reads canonical evidence and schedules; it does not own a second copy of source content.
- Every item retains stable account, Space, source, and version identifiers so retrieval, MCP, deletion, and provenance share the same boundary.
- All Spaces are private from other accounts and the public. For external-AI access they have one of two categorical states: an ordinary **non-private Space**, which is eligible for whole-account MCP reads, or an explicitly marked **Private Space**, which external AI and MCP must never read.
- New Spaces use the ordinary non-private state unless the user explicitly marks them Private. The distinction is visible wherever a Space is created, opened, or changed; it is an egress boundary, not a sharing/publication setting.
- Public publishing, teams, and classroom administration are outside the initial boundary.

## Alternatives

- Use folders/tags only: rejected because they do not provide a reliable authorization or provenance boundary.
- Put learning state inside each document: rejected because evidence often spans several sources and sessions.
- Make Learning a hidden dashboard projection: rejected because learning is a core user workflow, not analytics.

## Consequences

- Navigation has two named surfaces: Spaces for knowledge work and Learning for deliberate practice.
- Imports and integrations must ask for a destination Space.
- Native cross-Space search and Learning use account authorization. MCP federation follows the fixed whole-account/non-private contract in ADR 0007.

## Security effect

Space membership is enforced in application authorization and database policies, not only in UI routes. The Private flag is enforced before external-AI retrieval and cannot be overridden by a client grant. Derived learning signals inherit the strictest Space visibility involved in their evidence.

## Reversal strategy

The stable Space identifier remains the authorization key. New organization types or team containers can be layered above Spaces without rewriting documents or evidence; Learning can be split into additional views over the same ledger.

## Links

- [ADR 0002: PostgreSQL Evidence Ledger](0002-postgres-evidence-ledger.md)
- [ADR 0007: Whole-account MCP and private Spaces](0007-whole-account-mcp-and-private-spaces.md)
- [ADR 0012: Evidence Twin, event ledger, and FSRS](0012-evidence-twin-event-ledger-and-fsrs.md)
