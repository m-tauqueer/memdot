# Memdot documentation

Status: **Technical Phases 1–3 accepted; Waves 4–10 are implemented on `develop`.
Manual external configuration, the Alpha integration gate, and one final end-to-end
audit remain before release acceptance.**
Baseline date: **2026-07-17**

This directory is the source of truth for Memdot v1. It describes a general,
portable memory platform whose first deeply developed product mode is Learning.
Where a document describes a code path, service, command, or schema that does not
yet exist, it is explicitly labelled as target state. Phase 1 introduces verified
scaffold paths and commands only — not product behavior.

## Reading order

### Founder and product review

1. [Product Requirements Document](product/PRD.md)
2. [Functional Specification Document](product/FSD.md)
3. [ADR index](adr/README.md)
4. [Evaluation and release gates](technical/EVALUATION_RELEASE_GATES.md)

### Engineering implementation

1. [Execution Context](../CONTEXT.md)
2. [Implementation Plan](../IMPLEMENTATION_PLAN.md)
3. [Implementation Tracker](../IMPLEMENTATION_TRACKER.md)
4. [Product Requirements Document](product/PRD.md)
5. [ADR index](adr/README.md)
6. [System Architecture](technical/SYSTEM_ARCHITECTURE.md)
7. [Technical Requirements Document](technical/TRD.md)
8. [Security, Privacy, and Threat Model](technical/SECURITY_PRIVACY_THREAT_MODEL.md)
9. [Evaluation and Release Gates](technical/EVALUATION_RELEASE_GATES.md)
10. [Alpha Integration Gate](technical/ALPHA_INTEGRATION_GATE.md)

### AI agent orientation

1. Repository [AGENTS.md](../AGENTS.md)
2. [Execution Context](../CONTEXT.md)
3. [Implementation Plan](../IMPLEMENTATION_PLAN.md)
4. The active phase in [Implementation Tracker](../IMPLEMENTATION_TRACKER.md)
5. [Codebase Context Map](ai/CODEBASE_CONTEXT_MAP.md)
6. The relevant ADRs and owning product/technical requirements
7. The tests required by [Evaluation and Release Gates](technical/EVALUATION_RELEASE_GATES.md)

## Document map

| Document               | Owns                                                                               | Must not own                                                 |
| ---------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| PRD                    | Problem, users, product outcomes, scope, success                                   | Component-level implementation                               |
| FSD                    | Routes, user flows, states, rules, acceptance behaviour                            | Infrastructure topology                                      |
| TRD                    | Contracts, schemas, algorithms, SLOs, failure behaviour                            | Product positioning                                          |
| System Architecture    | Boundaries, ownership, trust zones, data and deployment flows                      | Screen-level copy                                            |
| ADRs                   | One durable architectural decision per record                                      | Repeated full specifications                                 |
| Security/Privacy       | Threats, controls, data lifecycle, incident gates                                  | Feature prioritisation                                       |
| Evaluation             | Corpora, metrics, hard gates, release process                                      | Product implementation                                       |
| Alpha Integration Gate | Live credentialed-provider and deployment proof before frontend authorization      | Fixture/emulator success as proof of external compatibility  |
| Codebase Context Map   | Target repository shape and safe AI-agent routing                                  | Unverified current-state claims                              |
| Implementation Tracker | Delivery waves, micro-phases, validation gates, and progress                       | Product or technical requirements that belong in PRD/FSD/TRD |
| Implementation Plan    | Wave/phase map, smoke schedule, reporting policy, and review boundary              | Transient prompts, reports, logs, or patches                 |
| Execution Context      | Verified current state, locked invariants, active phase, and durable agent context | Aspirational implementation claims                           |

## Locked product contract

- Memdot is a general memory platform; Learning is its first flagship mode.
- The hosted beta is public, free, Google-auth-only, and restricted to people
  confirming they are at least 18.
- The UI is English-first. English, Hindi, and Hinglish memory and retrieval are
  first-class v1 requirements.
- A connected AI receives one plainly disclosed whole-account read grant over
  all non-private spaces. Private spaces are an absolute exclusion.
- Native conversations are captured automatically. External capture is best
  effort through an explicit tool or import because an MCP server cannot observe
  a host's complete conversation by default.
- User content is retained until deletion. AI-derived claims and edits are
  proposals until the user approves them.
- The beta advertises no monthly per-user quota. Per-request limits, concurrency
  controls, abuse controls, backpressure, and system-wide safety breakers remain
  mandatory operational protections.
- The hosted service and the complete self-hosted product share public contracts.
  Tex and paid model providers are optional integrations, not prerequisites for
  functional parity.

## Requirement and decision identifiers

Identifiers are immutable after publication. Removed requirements are marked
`Retired`; their identifiers are never reused.

- `PRD-AREA-NNN`: product requirement grouped by product domain.
- `FSD-AREA-NNN`: functional behaviour or user-visible state.
- `TRD-AREA-NNN`: technical contract or invariant.
- `ADR-NNNN`: architectural decision.
- `EVAL-AREA-NNN`: evaluation or release gate.
- `SEC-AREA-NNN`: security/privacy control.

Each FSD requirement links to one or more PRD requirements. Each TRD contract
links to its PRD/FSD drivers and owning ADR. The evaluation document identifies
the gates that verify each critical contract.

## Shared glossary

| Term                 | Definition                                                                                     |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| Account              | One hosted or self-hosted user's top-level security boundary in v1.                            |
| Space                | General organisational and permission boundary. A space may be private from external AI.       |
| Learning space       | A space profile that adds courses, curriculum, assessment, evidence, and review.               |
| Source               | A user-authored or imported logical item across one or more immutable revisions.               |
| Source revision      | Immutable snapshot of source bytes/content plus provenance.                                    |
| Element              | Addressable unit in a parsed or authored document with a stable locator.                       |
| Memory record        | Approved user-authored or derived assertion, preference, episode, or insight.                  |
| Proposal             | Unapproved AI/external suggestion that is excluded from normal retrieval.                      |
| Evidence Ledger      | PostgreSQL-owned canonical state and append-only history.                                      |
| Projection           | Rebuildable representation in Tex, pgvector, search indexes, or read models.                   |
| Context Compiler     | Policy-aware pipeline that retrieves, validates, reranks, packs, and receipts evidence.        |
| Context receipt      | Explanation of the immutable evidence, revisions, policies, and retrieval route used.          |
| Evidence Twin        | Learning projection separating source coverage, demonstrated evidence, recall, and confidence. |
| Canonical            | Authoritative Memdot state; it does not mean an imported source is factually correct.          |
| Private space        | Space whose content is categorically ineligible for external-AI retrieval.                     |
| Capture completeness | `complete`, `partial`, `summary`, or `unknown` indication for imported external conversations. |

## Source hierarchy

1. Accepted owner decisions recorded in the PRD and ADRs.
2. Functional and technical contracts in the FSD/TRD.
3. This index, the architecture document, and supporting annexes.
4. External provider documentation.

When external documentation conflicts with a locked product invariant, the
integration must adapt or remain disabled; canonical ownership, private-space
exclusion, deletion, and self-host parity are not relaxed silently.

## Maintenance rule

Any change to product scope, a public interface, canonical ownership, privacy,
or a release gate must update all affected requirement links and either amend an
existing ADR or add a superseding ADR. Implementation paths and commands must be
added to the Codebase Context Map only after they exist and have been verified.
