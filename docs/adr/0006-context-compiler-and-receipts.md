# ADR 0006: Context Compiler and Receipts

- Status: Accepted
- Date: 2026-07-15

## Context

Useful tutoring requires combining sources, accepted memory, course structure, learner evidence, conversation state, permissions, and model constraints. Building prompts ad hoc inside features would make context inconsistent and impossible to audit.

## Decision

- All native AI and MCP context requests pass through a versioned **Context Compiler**.
- Inputs are caller identity, purpose, account/Space scope, user request, requested context classes, token budget, provider capability/residency, and policy version.
- The compiler performs authorization, retrieval, evidence ordering, contradiction and freshness checks, token budgeting, redaction, and output formatting.
- Output is a provider-neutral context bundle with instructions, evidence units and citations, learner-state summary when authorized, omissions, warnings, and provenance.
- Every compilation creates a **context receipt** containing request/purpose IDs, caller/client, granted scopes, canonical source/version and evidence IDs, compiler/retrieval versions, provider/model/region, token counts, omissions, timestamps, and hashes. Raw prompt or source text is not duplicated into the receipt.
- Receipts support user-visible “what was shared” explanations, debugging, deletion propagation, and evaluation. They are not a second transcript store.
- Compiler policy is deterministic where possible; the language model does not decide its own authorization or evidence scope.

## Alternatives

- Assemble prompts independently in each feature: rejected because privacy and quality behavior would drift.
- Save complete prompts indefinitely for replay: rejected because it duplicates sensitive data and frustrates deletion.
- Give the model tools and let it discover all context: rejected because authorization and cost become probabilistic.

## Consequences

- Product features share one inspectable context contract.
- Compiler versioning and golden tests become release-critical.
- Exact replay may require still-authorized canonical source versions; receipts alone intentionally cannot reconstruct deleted content.

## Security effect

Compilation is deny-by-default for every data class. Receipts are content-free, pseudonymous operational records with restricted access and declared retention. Provider and region are fixed before payload creation; no silent cross-provider fallback is allowed.

## Reversal strategy

Compiler versions can run in shadow mode and receipts make outputs comparable. A replacement must emit the same evidence/provenance contract before becoming active.

## Links

- [ADR 0005: Hybrid retrieval](0005-hybrid-retrieval.md)
- [ADR 0007: Whole-account MCP and private Spaces](0007-whole-account-mcp-and-private-spaces.md)
- [ADR 0010: India-regional inference and direct adapters](0010-india-regional-inference-and-direct-adapters.md)
