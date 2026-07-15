# Memdot Implementation Plan

Version: 1.0
Baseline date: 2026-07-15
Current status: Phase 1 corrections complete; revised report submitted; previous Codex verdict FAIL; correction round 2 pending re-audit
Execution model: Tauqueer owns decisions, Grok implements a complete phase, Codex audits at the phase boundary

## 1. Purpose

This is the authoritative execution sequence for turning the founding Memdot
specification into a production-ready implementation. It defines phase order,
documentation inputs, ownership boundaries, phase deliverables, validation, and
the Grok-to-Codex handoff.

The detailed task checklist remains in
[IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md). Current repository state
and durable invariants are summarized in [CONTEXT.md](CONTEXT.md).

## 2. Source-of-truth hierarchy

1. [PRD](docs/product/PRD.md) owns product intent, scope, promises, and outcomes.
2. [FSD](docs/product/FSD.md) owns routes, visible behavior, states, and
   acceptance scenarios.
3. [ADRs](docs/adr/README.md) own accepted architectural decisions.
4. [TRD](docs/technical/TRD.md) owns technical contracts, schemas, interfaces,
   SLOs, and failure behavior.
5. [System Architecture](docs/technical/SYSTEM_ARCHITECTURE.md) owns component,
   trust, data-flow, and deployment boundaries.
6. [Security and Privacy Threat Model](docs/technical/SECURITY_PRIVACY_THREAT_MODEL.md)
   owns adversarial controls and launch blockers.
7. [Evaluation and Release Gates](docs/technical/EVALUATION_RELEASE_GATES.md)
   owns quality thresholds and promotion gates.
8. [Codebase Context Map](docs/ai/CODEBASE_CONTEXT_MAP.md) owns intended and,
   after scaffolding, verified code ownership and dependency direction.
9. This plan owns execution order and phase boundaries.
10. [IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md) owns the detailed
    checklist inside each phase.

No execution document may weaken a higher-level product, security, technical,
or evaluation contract.

## 3. Phase-level working loop

1. Tauqueer explicitly starts one macro-phase.
2. Grok reads the phase documentation map and the complete phase checklist.
3. Grok executes every micro-phase in order.
4. At each micro-phase boundary, Grok runs the assigned self-checks, fixes any
   failures, records evidence in working notes, and continues without waiting
   for Codex.
5. Grok stops early only for a genuine owner decision, architecture
   contradiction, unavailable required credential/resource, unsafe external
   mutation, or blocker it cannot safely resolve.
6. After all micro-phases, Grok runs the complete phase exit gate.
7. Grok sends one consolidated phase report using
   [PHASE_REPORT_TEMPLATE.md](docs/execution/PHASE_REPORT_TEMPLATE.md), including
   the full diff and raw validation evidence.
8. Codex audits the entire phase against the documentation map and returns PASS,
   FAIL — CORRECTIONS REQUIRED, or BLOCKED — OWNER DECISION REQUIRED.
9. On FAIL, Grok fixes the same phase, reruns affected micro-checks and the
   complete phase gate, then resubmits.
10. Only a Codex PASS allows Tauqueer to authorize the commit and start the next
    phase.

## 4. Universal implementation rules

- PostgreSQL is canonical for authorization, revisions, evidence, events,
  proposals, receipts, deletion truth, and learner state.
- Immutable object storage is canonical for originals and parser artifacts.
- Tex, pgvector indexes, caches, projections, and model outputs are derived or
  proposed and must be rebuildable.
- Web and MCP never query PostgreSQL, object storage, Tex, or model vendors
  directly.
- Core owns canonical writes and product authorization.
- Workers own durable execution, never unsnapshotted session authorization.
- Provider outputs are candidates and are rejoined to canonical PostgreSQL data
  under RLS before use.
- Private Spaces never reach external AI through results, candidates, receipts,
  errors, caches, proposals, or captured interactions.
- AI writes and edits remain proposals until first-party approval.
- Conversation activity never automatically raises learning evidence.
- Every public item and citation resolves to an immutable canonical revision and
  a reauthorized first-party locator.
- Self-hosted Memdot must remain functional with Tex disabled, telemetry export
  off, and no paid model API.
- Accepted work is durable. Overload may queue, degrade, or reject before
  acceptance, but may not lose work or fabricate success.
- No commit, push, merge, deploy, credential rotation, paid resource creation,
  or production mutation occurs without Tauqueer's explicit authorization.

## 5. Documentation map by phase

| Phase | Primary documentation | Requirement families | Decisions | Verification owner |
|---|---|---|---|---|
| 1. Repository foundation | Context Map sections 2, 3, 11, 12; TRD sections 2 and 12; AGENTS | TRD-SYS-001..010, TRD-DEP-006..008 | ADR-0011 | Tracker Phase 1; documentation and scaffold CI |
| 2. Local/self-host platform | TRD sections 11..13; Architecture section 7; Threat Model sections 3, 8, 10 | TRD-DEP-004..008, TRD-SEC-005..007, TRD-OPS-009..013 | ADR-0010, ADR-0011 | Evaluation sections 11 and 12 |
| 3. Canonical ledger and identity | TRD section 3 and section 11; Architecture sections 5 and 16; FSD sections 4 and 7 | TRD-DATA-001..012, TRD-SEC-001, TRD-SEC-013, FSD-AUTH-*, FSD-ONB-* | ADR-0002, ADR-0007 | Threat Model sections 4 and 5; cross-account suite |
| 4. Core API and durable work | TRD sections 2.2, 3.2, 10, 13; Architecture sections 4 and 5 | TRD-API-001..008, TRD-OPS-004, TRD-OPS-009..010 | ADR-0002 | Evaluation sections 9 and 11 |
| 5. Ingestion and parsing | TRD section 5; Architecture section 8; FSD sections 6 and 9 | TRD-ING-001..018, TRD-DATA-007..012, FSD-ING-*, FSD-SRC-* | ADR-0004 | EVAL-ING-001..012 |
| 6. Documents and memory | TRD sections 3.2 and 4; Architecture section 11; FSD sections 8 and 14 | TRD-DOC-001..012, TRD-DATA-009..012, FSD-DOC-*, FSD-MEM-* | ADR-0008, ADR-0009 | Evaluation sections 5 and 10 |
| 7. Retrieval and context | TRD section 6; Architecture sections 9 and 15; FSD section 11 | TRD-RET-001..018, FSD-ASK-* | ADR-0003, ADR-0005, ADR-0006, ADR-0010 | Evaluation sections 4, 5, 7, 8, 11 |
| 8. Learning backend | PRD sections 4.2, 4.3, 6.2; TRD section 7; Architecture section 12; FSD sections 12 and 13 | PRD-LEARN-001..007, TRD-LRN-001..014, FSD-TST-*, FSD-REV-* | ADR-0012 | EVAL-LRN-001..008 |
| 9. MCP and conversations | TRD sections 9 and 10; Architecture sections 10 and 16; FSD sections 14 and 15 | TRD-MCP-001..012, TRD-API-001..005, FSD-INT-*, FSD-MEM-008..009 | ADR-0007, ADR-0008 | Evaluation section 9; Threat Model sections 4, 6, 7 |
| 10. Notion and lifecycle | TRD sections 8 and 11; Architecture sections 13 and 14; FSD sections 10 and 17 | TRD-NOT-001..012, TRD-SEC-008..011, FSD-NOT-*, FSD-EXP-* | ADR-0002, ADR-0003, ADR-0014 | Evaluation sections 10 and 11; Threat Model section 9 |
| 11. Hardening and deployment | TRD sections 11..14; Architecture sections 6, 7, 17, 18; complete Threat Model | TRD-SEC-001..014, TRD-DEP-001..008, TRD-OPS-001..013 | ADR-0010, ADR-0011 | Complete Evaluation and Release Gates |
| 12. Frontend foundation | FSD sections 2..5, 18, 19; TRD sections 2 and 11; Architecture section 7 | FSD-NAV-*, FSD-AUTH-*, FSD-ONB-*, FSD-ERR-*, FSD-A11Y-* | ADR-0013 | Evaluation section 10 |
| 13. General Memory frontend | FSD sections 5..11 and 14; corresponding TRD data, document, ingestion, retrieval contracts | FSD-TOD-*, FSD-LIB-*, FSD-SRC-*, FSD-SPC-*, FSD-DOC-*, FSD-ING-*, FSD-ASK-*, FSD-MEM-* | ADR-0001, ADR-0004, ADR-0006, ADR-0009 | Evaluation sections 3, 5, 7, 10 |
| 14. Learning and integrations frontend | FSD sections 12..20; corresponding TRD learning, MCP, Notion, security contracts | FSD-TST-*, FSD-REV-*, FSD-INT-*, FSD-SET-*, FSD-EXP-*, FSD-OFF-*, FSD-A11Y-* | ADR-0007, ADR-0008, ADR-0012, ADR-0013, ADR-0014 | Evaluation sections 6, 9, 10, 11 |
| 15. Release candidate | PRD section 14; FSD section 21; TRD section 14; Architecture section 19; Threat Model section 12 | FSD-AC-001..024 and all implemented requirements | All accepted ADRs | Complete Evaluation and Release Gates |

## 6. Implementation phases

### Phase 1 — Repository foundation and production-grade monorepo

Goal: Convert the documentation-only workspace into a deterministic,
production-grade monorepo without implementing product behavior.

Micro-phases:

1. Repository and workspace scaffold.
2. Service and package skeletons.
3. Contract and schema generation toolchain.
4. CI, repository hygiene, documentation synchronization, and verified commands.

Required result:

- Intended ownership boundaries exist as real paths.
- TypeScript and Python toolchains are pinned and reproducible.
- Web, MCP, Core, workers, model router, contracts, domain, and UI packages
  build as minimal skeletons.
- Dependency direction is automatically enforced.
- OpenAPI, JSON Schema, event schemas, and generated TypeScript contracts have a
  single deterministic owner.
- Containers are non-root, minimal, and health-checkable.
- CI-equivalent validation and documentation validation pass.
- AGENTS and Codebase Context Map contain verified paths and commands.

Phase 1 starts with
[PHASE_01_GROK_PROMPT.md](docs/execution/PHASE_01_GROK_PROMPT.md).

### Phase 2 — Self-host infrastructure and local developer platform

Goal: Establish the complete production-like, Tex-disabled local platform before
domain implementation.

Micro-phases:

1. Compose topology and isolated networks.
2. Typed configuration, local TLS, OIDC, and secret encryption.
3. Persistence, backup/restore, restart, health, and operational smoke tests.

Required result:

- Caddy, web, API, MCP, workers, model router, Hatchet, PostgreSQL and pgvector,
  SeaweedFS, Keycloak, OpenBao, and observability start from documented commands.
- Tex is disabled by default.
- Secrets are referenced or encrypted and never logged.
- Internal stores are not exposed publicly.
- Restart, persistence, backup, restore, and telemetry-off self-host smoke pass.

### Phase 3 — Canonical PostgreSQL ledger, tenancy, identity, and authorization

Goal: Make PostgreSQL the enforceable ownership and evidence boundary.

Micro-phases:

1. Alembic and tenancy schema.
2. Evidence-ledger foundations and immutable records.
3. Google-only hosted authentication, self-host OIDC, 18+ activation, sessions,
   CSRF, and recent authentication.
4. RLS and cross-account adversarial suite.

Required result:

- Every account-owned table carries correct ownership and FORCE RLS.
- Cross-account attachment, read, write, pagination, and error inference fail.
- Product authorization remains outside the identity broker.
- Hosted Google authentication and adult activation work without collecting date
  of birth or identity documents.
- Immutable revisions, append-only events, conflicts, outbox, idempotency, and
  canonical pointers are structurally enforced.

### Phase 4 — Core API, durable transactions, workflows, and object storage

Goal: Establish the canonical write path and crash-safe long-running work.

Micro-phases:

1. FastAPI policy, request context, errors, cursors, and backpressure.
2. Idempotency, transactional outbox, Hatchet workflows, retries, and dead-letter
   behavior.
3. Immutable object-storage port and presigned upload.
4. Generated service clients, event integration, and crash-recovery tests.

Required result:

- Public errors, pagination, authorization, idempotency, and durable 202 jobs
  match TRD contracts.
- Canonical mutations and committed-fact events are atomic.
- Worker replay converges without duplicate canonical effects.
- Uploads are direct, immutable, hash-verified, account-bound, and retryable.
- Dependency failure cannot fabricate acceptance or widen access.

### Phase 5 — Source ingestion, parsing, OCR, normalization, and reprocessing

Goal: Produce deterministic, provenance-complete source revisions from every
supported v1 input.

Micro-phases:

1. Ingestion intent, upload, source, revision, and durable status.
2. Parser-neutral normalization and deterministic structural IDs.
3. Confidence, English/Hindi/Hinglish OCR, and gated fallback.
4. Shadow reprocessing, atomic promotion, projection events, and parser
   evaluation.

Required result:

- Originals, immutable source revisions, normalized structures, locators,
  warnings, and statuses are honest and durable.
- Same input and profile produce identical revision, element, and chunk IDs.
- No missing page is reported successful.
- EVAL-ING-001..012 pass for blocking corpus slices.
- Reprocessing never replaces a valid active run before shadow validation.

### Phase 6 — Rich documents, canonical memory, conflicts, and proposed writes

Goal: Establish Memdot-owned rich-document and memory truth without silent
overwrites or model commits.

Micro-phases:

1. MemdotDocument v1 schema, serialization, sanitization, and migrations.
2. Immutable document revisions and stale-base conflict handling.
3. Memory ontology, provenance, relations, and conflict sets.
4. Memory and AI document-patch proposal state machines.

Required result:

- MemdotDocument round-trips exactly and preserves unknown nodes.
- Saves are revisioned, idempotent, and conflict-safe.
- Truth class, provenance, current/history, and conflicts stay explicit.
- AI and external-agent writes remain pending until first-party approval.
- Pending/rejected proposals never enter normal retrieval or learning evidence.

### Phase 7 — Retrieval, Context Compiler, model routing, Tex, and OSS fallback

Goal: Compile authorized, version-correct, conflict-aware evidence independently
of any single semantic provider.

Micro-phases:

1. Exact, temporal, graph, and local semantic provider lanes.
2. Query planning, fusion, reranking, and canonical post-filter.
3. Context Compiler, citations, conflict detection, budget packing, and receipts.
4. Model router, Tex adapter, outage fallback, rebuild, and frozen benchmarks.

Required result:

- Retrieval and context meet EVAL-RET and context thresholds.
- Every provider candidate is reauthorized and version-checked in PostgreSQL.
- External knowledge is labelled and cannot become source truth.
- Context receipts identify evidence, versions, conflicts, omissions, and routes.
- Tex outage preserves exact, graph, temporal, pgvector, and local-rerank
  functionality with identical security and citation behavior.

### Phase 8 — Learning backend, Evidence Twin, assessment, and FSRS

Goal: Build source-grounded deliberate learning whose state can be replayed from
eligible append-only events.

Micro-phases:

1. Course, syllabus, concept, prerequisite, and source-coverage graph.
2. Versioned MCQ, short-answer, written assessment, confidence, and sealed
   grading.
3. Learner event ledger, evidence eligibility, Evidence Twin, and FSRS.
4. Learning benchmarks and delayed-success measurement.

Required result:

- Confirmed prerequisite graph has zero cycles and complete provenance.
- Answers and rubrics never leak before submission.
- Event replay is deterministic under duplicates and reordering.
- Hinted, revealed, post-feedback, ungradable, or conversation-derived events
  never establish demonstrated learning.
- EVAL-LRN-001..008 pass.

### Phase 9 — MCP, OAuth, external AI, conversations, and capture

Goal: Expose portable whole-account non-private memory without weakening private,
proposal, conversation, or learner boundaries.

Micro-phases:

1. OAuth-protected Streamable HTTP MCP edge.
2. OpenAI-compatible search and fetch.
3. prepare_context, propose_memory, and record_interaction.
4. Native/external conversation ledger and completeness.

Required result:

- All five frozen MCP tools pass schemas, authorization, errors, idempotency, and
  side-effect tests.
- search and fetch use stable canonical IDs and absolute reauthorized URLs.
- memdot.memory.read covers all current/future non-private Spaces but never
  Private Spaces, pending proposals, incomplete attempts, or sealed answers.
- External capture remains explicitly best-effort.
- Interaction capture never changes learner evidence.

### Phase 10 — Notion synchronization, export, deletion, and restore safety

Goal: Implement bounded external synchronization and a complete user-controlled
data lifecycle.

Micro-phases:

1. Notion connection and selected-page inbound sync.
2. Dedicated Memdot-root two-way sync and three-way conflict handling.
3. Portable item, conversation, Space, and account export.
4. Immediate tombstone, durable purge, backup expiry, and restore replay.

Required result:

- Selected pages outside the Memdot root are never modified remotely.
- Approved Memdot-authored documents under the root sync idempotently.
- Concurrent changes never use silent last-write-wins.
- Export contains portable canonical data, originals, history, events, citations,
  completeness, hashes, and warnings.
- Deleted data becomes immediately unavailable and cannot resurrect after
  restore, reimport, retry, or reprojection.

### Phase 11 — Security hardening, observability, deployment, and evaluation

Goal: Make the backend/platform release-capable before frontend product work.

Micro-phases:

1. Threat controls, telemetry allowlist, admin controls, and incident runbooks.
2. Circuit breakers, backpressure, SLOs, metrics, alerts, and failure injection.
3. India-first hosted GCP infrastructure.
4. Supply-chain integrity, self-host parity, and benchmark automation.

Required result:

- Telemetry contains no prompts, responses, source text, filenames, answers,
  cookies, credentials, or authorization headers.
- Overload and provider failures queue, degrade, or reject safely.
- Hosted content and managed inference remain in Mumbai; Delhi holds encrypted
  disaster-recovery backups only.
- Images/dependencies are pinned, scanned, SBOM-generated, signed, and
  reproducible.
- Tex-disabled, telemetry-off self-host acceptance passes.
- Benchmarks produce reproducible artifacts and hashes.

### Phase 12 — Frontend foundation, authentication, responsive shell, and PWA

Goal: Begin frontend work only after backend contracts and operational behavior
are real and verified.

Micro-phases:

1. Next.js architecture and generated Core client.
2. Authentication, adult confirmation, onboarding, sessions, and recent auth.
3. Accessible design system, route shells, global states, and responsive
   navigation.
4. Installable PWA and encrypted offline foundation.

Required result:

- Frontend consumes generated contracts and contains no provider or
  authorization shortcuts.
- Hosted Google auth, 18+, onboarding, logout, session failure, and recent-auth
  flows pass.
- Every v1 route has an accessible responsive shell and explicit states.
- Offline cache is opt-in, encrypted, account-partitioned, and cleared on logout.

### Phase 13 — General Memory frontend, editor, ingestion, Ask, and Memory

Goal: Deliver complete first-party General Memory workflows over verified backend
contracts.

Micro-phases:

1. Today, Library, Spaces, Private Spaces, and source detail.
2. Upload, processing, failure, reprocess, and global jobs.
3. Tiptap/MemdotDocument editor, history, stale-base conflicts, and AI patches.
4. Ask, search, citations, context receipts, Memory, proposals, and activity.

Required result:

- All related FSD routes, states, and acceptance behaviors pass.
- History and conflicts stay visible.
- AI changes remain reviewable proposals.
- Source-first answers cite immutable evidence and label External knowledge.
- Editor round-trip, XSS, concurrency, recovery, citation, accessibility, and
  responsive suites pass.

### Phase 14 — Learning, integrations, settings, offline, and accessibility

Goal: Complete the Learning flagship and all consent, lifecycle, offline, and
accessibility surfaces.

Micro-phases:

1. Learning setup, syllabus map, concepts, prerequisites, and coverage.
2. Test, results, Review, Evidence Twin, confidence, and due reasons.
3. MCP, Notion, provider, BYOK, privacy, and settings surfaces.
4. Export, deletion, global status, pinned reading, offline review, and complete
   accessibility/browser matrix.

Required result:

- Learning UI preserves sealed answers and evidence eligibility.
- Whole-account MCP consent and Private-Space exclusion are explicit.
- Notion write boundary and conflicts are visible.
- Offline is limited to pinned reading and seven-day review packs.
- Supported browsers, installed PWA, keyboard, screen reader, touch, zoom,
  responsive, and WCAG-oriented gates pass.

### Phase 15 — Release candidate and beta launch readiness

Goal: Prove the complete product against every founding acceptance, security,
quality, operational, legal, and portability promise.

Micro-phases:

1. FSD-AC-001..024 and cross-document end-to-end acceptance.
2. Frozen benchmarks, performance, and adversarial security.
3. Live MCP/Notion/provider compatibility, restore, deployment, and incident
   rehearsal.
4. Documentation, licensing, legal review, founder QA, and release decision.

Required result:

- Every hard release gate passes its absolute threshold.
- At least 10,000 adversarial cross-account/Private-Space calls produce zero
  leakage.
- Search, fetch, context, tool success, ingestion, projection, revoke, RPO, and
  RTO targets pass.
- ChatGPT, Claude remote MCP, Gemini CLI, and authorized Notion test-workspace
  gates pass before those compatibility claims are made.
- Restore replay proves deleted data cannot resurrect.
- No critical security, privacy, data-integrity, citation, learning-integrity,
  deletion, accessibility, or self-host blocker remains.
- Codex returns final PASS and Tauqueer makes the explicit launch decision.

## 7. Phase report and audit evidence

Every phase report must contain:

- phase number, branch, base commit, and repository state;
- implemented scope and explicit non-goals;
- requirement and ADR traceability;
- micro-phase self-check results;
- complete changed-file inventory;
- migrations, public contracts, generated files, events, and compatibility
  effects;
- commands and unedited terminal output;
- test counts, skipped tests, coverage, benchmark/profile hashes, and performance
  evidence;
- security/privacy and failure-mode impact;
- documentation changes;
- git status, diff stat, diff check, and complete reviewable diff;
- known limitations and blockers;
- confirmation that no unauthorized commit, push, merge, deploy, credential
  rotation, paid resource, or production mutation occurred.

Codex audits the complete phase, not Grok's summary alone.

## 8. Current execution pointer

- Active phase: Phase 1 — corrections complete; revised report submitted; correction round 2 pending Codex re-audit.
- Phase prompt: [PHASE_01_GROK_PROMPT.md](docs/execution/PHASE_01_GROK_PROMPT.md).
- Current implementation: Phase 1 monorepo scaffold candidate (no product domain).
- Current code commands: verified in AGENTS.md / Codebase Context Map.
- Current phase report: revised consolidated Grok Phase 1 report submitted (awaiting round-2 re-audit).
- Current Codex verdict: FAIL — CORRECTIONS REQUIRED (prior round); documentation pointer alignment pending re-audit.
- Previous Codex verdict: FAIL — CORRECTIONS REQUIRED (substantive gates later PASS; docs/engine inconsistency remained).
- Current accepted implementation commit: none.
