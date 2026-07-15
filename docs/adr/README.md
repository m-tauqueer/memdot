# Memdot Architecture Decision Records

This directory records accepted product and architecture decisions for Memdot. Later changes must supersede an ADR explicitly rather than silently weakening its guarantees.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-spaces-and-learning.md) | Spaces and Learning | Accepted |
| [0002](0002-postgres-evidence-ledger.md) | PostgreSQL Evidence Ledger | Accepted |
| [0003](0003-tex-replaceable-projection.md) | Tex as a replaceable projection | Accepted |
| [0004](0004-parser-neutral-document-model.md) | Parser-neutral document model | Accepted |
| [0005](0005-hybrid-retrieval.md) | Hybrid retrieval | Accepted |
| [0006](0006-context-compiler-and-receipts.md) | Context Compiler and receipts | Accepted |
| [0007](0007-whole-account-mcp-and-private-spaces.md) | Fixed whole-account MCP read and categorical Private Spaces | Accepted |
| [0008](0008-proposed-writes-and-best-effort-interaction-capture.md) | Proposed writes and best-effort interaction capture | Accepted |
| [0009](0009-tiptap-and-memdotdocument.md) | Tiptap and MemdotDocument | Accepted |
| [0010](0010-india-regional-inference-and-direct-adapters.md) | India-regional inference and direct adapters | Accepted |
| [0011](0011-apache-2-and-self-host-parity.md) | Apache-2.0 and self-host parity | Accepted |
| [0012](0012-evidence-twin-event-ledger-and-fsrs.md) | Evidence Twin, event ledger, and FSRS | Accepted |
| [0013](0013-pwa-offline-boundary.md) | Pinned-reading and seven-day review-pack offline boundary | Accepted |
| [0014](0014-dedicated-notion-sync-area.md) | Dedicated-root Notion sync | Accepted |

## Reading order

The records are numbered by dependency. ADRs 0001-0004 establish the product and canonical data boundaries; ADRs 0005-0008 define retrieval and agent exchange; ADRs 0009-0011 define clients, providers, and distribution; ADRs 0012-0014 define the learning model and bounded product integrations.
