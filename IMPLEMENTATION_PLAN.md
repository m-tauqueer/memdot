# Memdot implementation plan

Version: 2.0
Approved: 2026-07-16
Execution model: 10 delivery waves, backend first, frontend last

## 1. Purpose

This plan converts the accepted PRD, FSD, TRD, architecture, ADR, security, and
evaluation documents into an execution sequence for Grok, Codex, and Tauqueer.
It deliberately minimizes slow handoffs while preserving the product's security,
canonical-data, self-hosting, and learning-integrity guarantees.

The original technical Phase IDs remain stable because requirements, tests, and
the two approved smoke checkpoints refer to them. Implementation is accelerated
by grouping those phases into ten larger delivery waves:

| Wave | Technical phases | Delivery boundary | State |
|---|---:|---|---|
| 1 | 1 | Repository and monorepo foundation | Accepted |
| 2 | 2 | Self-host platform and local operations | Accepted |
| 3 | 3 | Canonical PostgreSQL, tenancy, identity, and RLS | Accepted |
| 4 | 4–5 | Core runtime, durable workflows, object storage, and ingestion | Next |
| 5 | 6–7 | Documents, memory, retrieval, Context Compiler, models, and Tex | Pending |
| 6 | 8 | Learning backend and first full-system checkpoint | Pending |
| 7 | 9–10 | MCP, conversations, Notion, export, and deletion | Pending |
| 8 | 11 | Security, hosted deployment, evaluation, and pre-frontend checkpoint | Pending |
| 9 | 12 | Frontend foundation, authentication, shell, and PWA | Pending |
| 10 | 13–15 | Complete product frontend, acceptance, and beta readiness | Pending |

One delivery wave is one Grok implementation run, one consolidated chat report,
one Codex audit, and one owner-controlled commit decision.

## 2. Authority and handoff loop

1. Tauqueer explicitly authorizes one delivery wave.
2. Codex provides the full implementation prompt in chat. Prompts are not stored
   as repository documents.
3. Grok completes every micro-phase in the wave, self-checks each micro-phase,
   fixes its own failures, and continues without waiting for Codex.
4. Grok runs the wave's fast exit gate and posts one consolidated report in chat.
   Reports, raw logs, patches, and inventories are not committed under `docs/`.
5. Codex inspects the actual repository, diff, contracts, migrations, and test
   evidence and returns `PASS`, `FAIL — CORRECTIONS REQUIRED`, or
   `BLOCKED — OWNER DECISION REQUIRED`.
6. On the first failure, Codex provides one detailed correction prompt in chat.
7. Grok applies that correction prompt and returns one revised chat report.
8. If material logic gaps remain after that correction round, Tauqueer may ask
   Codex to correct the repository directly. Codex does not silently take over.
9. A passing review makes the wave eligible for Tauqueer's commit authorization.
   It never authorizes push, merge, deploy, credentials, paid resources,
   production mutation, or the next wave automatically.

## 3. Repository documentation policy

Repository documentation contains only durable source of truth:

- product and functional requirements;
- technical contracts and architecture;
- accepted ADRs;
- security/privacy and evaluation gates;
- current implementation context and codebase map;
- this plan and the implementation tracker;
- operator and subsystem documentation that engineers need after implementation.

The following are chat or `/tmp` artifacts and must not be committed:

- Grok prompts and correction prompts;
- phase/wave reports;
- candidate patches and patch statistics;
- changed-file inventories;
- copied terminal output and transient test logs;
- Codex audit narratives that do not change durable architecture or operation.

Durable behavior or architecture discovered during a review must update the
owning PRD/FSD/TRD/ADR, operator document, context, or codebase map directly.

## 4. Fast-mode and multitask rules

Grok may use multitask/parallel mode inside an authorized wave.

Safe parallel work includes:

- independent service or package implementation;
- fixtures, benchmark corpora, and independent test suites;
- provider adapters behind already frozen ports;
- documentation validation and generated-contract freshness;
- read-only research and codebase inspection.

The following have one writer at a time:

- Alembic migration chain and canonical schema;
- RLS policies, authentication, grants, deletion, and restore truth;
- OpenAPI and public MCP contracts;
- event versions and idempotency semantics;
- shared Compose, secrets, networking, and CI configuration;
- MemdotDocument schema and canonical revision protocol;
- learner-event eligibility and Evidence Twin projection rules.

Every parallel task receives exact file ownership, inputs, outputs, invariants,
and tests. Grok must reconcile all results in the main task, inspect the combined
diff, regenerate contracts once, and run one integrated fast exit gate.

Parallel tasks may not commit, create competing migrations, modify the same
contract independently, or declare the wave complete individually.

## 5. Validation and smoke policy

### 5.1 Per-micro-phase self-check

Each micro-phase ends with the smallest relevant checks: focused unit tests,
typing, schema validation, migration convergence, contract generation,
authorization probes, fixture benchmarks, or component builds. Grok fixes these
before starting the next micro-phase.

### 5.2 Per-wave fast exit gate

Every wave must finish with:

- formatting, lint, dependency boundaries, and type checks;
- all affected unit, integration, contract, migration, and adversarial tests;
- generated OpenAPI/schema/event freshness and compatibility checks;
- docs links, Mermaid, whitespace, secret scan, and `git diff --check`;
- build/import checks for affected workspaces;
- no skipped/focused tests unless the tracker explicitly permits them;
- one clean diff against the wave baseline.

These gates may use a temporary PostgreSQL container, local object-storage test
double, or bounded service component. They must not start the complete self-host
stack unless the wave explicitly owns a full smoke checkpoint.

### 5.3 Full self-host smoke schedule

Only two future full `make selfhost-smoke` runs are scheduled before frontend:

1. **Checkpoint A — after technical Phase 8, at the end of Wave 6.** It proves
   the complete backend through learning: Core API, durable jobs, object storage,
   ingestion, documents, memory, retrieval, Tex-disabled fallback, model routing,
   and learner-event replay.
2. **Checkpoint B — after technical Phase 11, at the end of Wave 8.** It proves
   MCP/lifecycle additions, security hardening, observability, hosted/self-host
   configuration, deletion/restore safety, and the stable backend contract before
   frontend implementation starts.

No full smoke runs occur in Waves 4, 5, or 7. Those waves use focused component
and integration gates. A correction round does not repeat a successful full
smoke unless the correction changes a smoke-owned seam.

Smoke-owned seams are Compose topology, service startup/readiness, networking,
TLS, OIDC discovery, secrets, runtime database-role wiring, migration job,
Hatchet durability/restart, object-store persistence, backup/restore, deletion
tombstone replay, telemetry-off boot, or Tex-disabled system fallback.

An exception smoke requires a concrete Codex finding that focused tests cannot
prove. Resource pressure, an unrelated project, or an unchanged external state
is not a reason to loop the smoke. Capture one successful log in `/tmp`, report
the command and result in chat, then stop.

## 6. Delivery-wave implementation map

### Wave 1 — Technical Phase 1: repository foundation

State: accepted.

Delivered the deterministic pnpm/uv monorepo, service/package skeletons,
dependency boundaries, generated contract toolchain, non-root images, CI, and
verified repository commands.

### Wave 2 — Technical Phase 2: self-host platform

State: accepted.

Delivered Tex-disabled Compose, local TLS/OIDC, OpenBao, PostgreSQL/object
storage/Hatchet foundations, readiness, persistence, backup/restore, and
operational safeguards.

### Wave 3 — Technical Phase 3: canonical data and authorization

State: accepted at commit `e77b299`.

Delivered frozen Alembic schema, separate database roles, FORCE RLS, signed
tenant context, canonical tenancy/ledger foundations, atomic pointer/outbox
writes, server-side OIDC code + PKCE, sessions/CSRF/18+, and seeded adversarial
authorization tests.

### Wave 4 — Technical Phases 4–5: Core runtime and ingestion

Goal: create the reusable backend execution plane and deterministic source
pipeline before documents, retrieval, learning, or external tools depend on it.

Documentation map:

- PRD: Core, portability, privacy, operations, ingestion requirements.
- FSD: authentication errors, source upload/status/reprocess/version states,
  global jobs, partial/degraded/rate-safe behavior.
- TRD: `TRD-API-*`, `TRD-SYS-*`, `TRD-OPS-*`, `TRD-DATA-*`, `TRD-ING-*`.
- ADRs: 0002, 0004, 0010, 0011.
- Security: tenant context, file handling, prompt/content isolation, secrets,
  abuse/backpressure, provider egress.
- Evaluation: API, workflow durability, parser corpus, OCR, provenance, SLOs.

Micro-phases:

1. Core transaction/request policy: authenticated context, correlation IDs,
   problem+json, signed pagination, idempotency keys, request limits, and safe
   non-enumerating errors.
2. Durable mutations: transactional outbox, leases, retries, jitter, dead-letter
   state, job/attempt APIs, cancellation, accepted-work durability, and replay.
3. Object storage: immutable original/snapshot/artifact keys, presigned transfer,
   checksum verification, quarantine, lifecycle, and provider-neutral port.
4. Source API: create/complete/status/reprocess/version/fetch flows with
   deterministic revisions, citations, authorization, and visible failure states.
5. Ingestion workflows: MIME sniffing, limits, malware seam, native extraction,
   Docling, gated OCR fallback, Hindi/Hinglish hints, stage checkpoints, retry,
   and content-minimized errors.
6. Canonical normalization: parser-neutral elements, locators, assets, tables,
   formulas, provenance, shadow parser runs, quality gate, and atomic promotion.
7. Integrated fast gate: API contracts, migration drift, outbox/job durability,
   object-store fixtures, parser golden corpus, RLS, failure injection, and
   documentation synchronization. No full self-host smoke.

Exit result:

- accepted jobs cannot disappear or report false success;
- identical source snapshots produce deterministic immutable revisions;
- every element has source revision and locator provenance;
- reprocessing preserves history and promotes only validated output;
- Core remains canonical and self-host works without paid parsing/model APIs.

### Wave 5 — Technical Phases 6–7: documents, memory, and context

Goal: implement canonical authored knowledge and the policy-aware retrieval stack
that will serve native UI, learning, and external AI.

Documentation map:

- PRD: General Memory Core, source-first answers, proposed writes, portability.
- FSD: document authoring/history/conflicts, Ask, Memory, proposals, citations,
  historical versions, source conflicts, degraded retrieval.
- TRD: `TRD-DOC-*`, `TRD-MEM-*`, `TRD-RET-*`, `TRD-MOD-*`, context receipts.
- ADRs: 0003, 0004, 0005, 0006, 0008, 0009, 0010.
- Security/Evaluation: injection resistance, canonical rejoin, retrieval corpus,
  citation quality, Tex/OSS parity, model egress.

Micro-phases:

1. Freeze `MemdotDocument v1`: block/inline/assets/marks schema, stable IDs,
   validation, migrations, JSON round-trip, HTML/Markdown import/export adapters,
   and XSS-safe rendering contract.
2. Authored-document protocol: immutable revisions, base revision, atomic pointer
   and outbox update, idempotent save, history, stale-base conflict, and recovery.
3. Canonical memory: assertions, provenance, supersession, retraction, conflicts,
   proposals, approval/rejection/edit audit, and retrieval exclusion until approval.
4. Retrieval projections: exact/lexical, temporal, graph, pgvector/local semantic,
   rebuild cursors, version/deletion filtering, and deterministic projection IDs.
5. Model-router and provider adapters: direct adapters, policy routing, structured
   output validation, timeouts/budgets, BYOK boundary, injection-safe payloads,
   and content-minimized logs.
6. Tex adapter: replaceable projection only, integration gate, outage/circuit
   breaker, reconciliation, rebuild, and fully functional Tex-disabled fallback.
7. Context Compiler: intent, scope, lanes, fusion, reranking, canonical RLS
   rejoin, conflicts, temporal/as-of mode, budget packing, citations, omissions,
   and receipt persistence without chain-of-thought.
8. Integrated fast gate: document fixtures, proposal invariants, retrieval slices,
   citation correctness, zero private/cross-account leakage, Tex/local parity,
   outage fallback, and model-policy tests. No full self-host smoke.

Exit result:

- rich JSON and immutable revisions are canonical;
- AI changes remain proposals;
- every retrieved item is reauthorized and source/revision grounded;
- Tex improves recall but never owns truth, authorization, or availability.

### Wave 6 — Technical Phase 8: learning backend and Checkpoint A

Goal: build replayable, source-grounded learning on the accepted memory/context
core, then run the first full backend smoke.

Documentation map:

- PRD Learning mode and delayed-success metric.
- FSD course setup, syllabus, Ask/Test/Review, confidence, results, Evidence Twin.
- TRD learning graph, assessment, event ledger, projections, and FSRS.
- ADRs: 0001, 0012, 0013.
- Security/Evaluation: sealed answers, evidence eligibility, replay, offline events,
  learning benchmark and delayed novel-item success.

Micro-phases:

1. Course/curriculum graph, objectives, concepts, prerequisite confirmation,
   source coverage, syllabus mapping, provenance, and cycle prevention.
2. Versioned assessment items/rubrics for MCQ, short answer, and written response;
   sealed answers; confidence-before-feedback; deterministic grading seams.
3. Append-only learner events with idempotent attempt/submission/reveal/hint/
   grading/review semantics and explicit eligibility classification.
4. Evidence Twin replay: demonstrated evidence, coverage, recall, confidence,
   provisional state, explanations, and projection rebuild.
5. FSRS scheduling with deterministic due state, bounded offline review packs,
   duplicate/reordered event handling, and no chat-derived mastery.
6. Learning benchmark: leakage, hints/reveals, replay properties, scheduling,
   Hindi/Hinglish content, and delayed source-grounded novel-item success.
7. Fast gates first, then exactly one successful `make selfhost-smoke` Checkpoint A.

Exit result:

- learner state rebuilds from eligible events;
- sealed material never leaks before submission/reveal;
- ineligible activity cannot increase demonstrated learning;
- the complete backend through learning survives the full system smoke.

### Wave 7 — Technical Phases 9–10: external access and lifecycle

Goal: expose eligible memory safely to external AI, synchronize bounded Notion
content, and implement export/deletion without weakening canonical truth.

Documentation map:

- PRD portability, integrations, privacy, self-hosting, and lifecycle.
- FSD Integrations, consent, context receipts, capture completeness, Notion,
  export, deletion, recovery, and all failure states.
- TRD MCP/OAuth, REST, conversations, sync, export, deletion, and restore.
- ADRs: 0007, 0008, 0014.
- Security/Evaluation: whole-account grants, private exclusion, OAuth attacks,
  prompt injection, deletion non-resurrection, connector compatibility.

Micro-phases:

1. OAuth-protected Streamable HTTP MCP with metadata, PKCE, scopes, issuer/
   audience/resource validation, rotation, revocation, and safe errors.
2. Frozen `search` and `fetch` company-knowledge shapes with canonical IDs,
   absolute reauthorized URLs, pagination, citations, and compatibility tests.
3. `prepare_context`, `propose_memory`, and `record_interaction` with validation,
   idempotency, receipts, proposal-only writes, completeness labels, and no
   learner-evidence side effect.
4. Native/external conversation ledger, retention, deletion, partial/summary/
   unknown capture, and explicit MCP isolation limitations.
5. Notion connection, selected-page inbound import, deterministic snapshots,
   pagination/rate handling, asset capture, and dedicated-root ownership rules.
6. Dedicated-root two-way sync with base versions, outbound idempotency,
   three-way conflicts, per-item pause, and no silent last-write-wins.
7. Portable export and deletion: originals, history, events, citations, hashes,
   tombstones, immediate invisibility, provider purge, backup expiry, restore
   replay, and protection from reimport/retry/reprojection resurrection.
8. Integrated fast gate: tool schemas, external/private adversarial matrix,
   Notion fixtures, revocation, export verification, deletion/restore drill, and
   conversation completeness. No full self-host smoke.

### Wave 8 — Technical Phase 11: release backend and Checkpoint B

Goal: harden and prove the complete backend/platform before any product frontend
is built.

Documentation map:

- PRD operational, privacy, OSS, self-host, hosted beta, and launch risks.
- FSD degraded/rate-safe/incident/account lifecycle behavior.
- TRD security, deployment, telemetry, SLO, backup, regional inference, and
  incident contracts.
- ADRs: 0010, 0011 and every operational consequence from 0002–0014.
- Full Security/Privacy Threat Model and Evaluation/Release Gates.

Micro-phases:

1. Complete threat controls, telemetry allowlist, audit minimization, secret
   rotation, admin boundaries, rate/abuse protections, and incident runbooks.
2. Backpressure, circuit breakers, overload behavior, SLO metrics, alerts,
   failure injection, queue/job visibility, and safe degradation.
3. India-first hosted GCP topology, Mumbai content/inference, Delhi encrypted DR,
   IAM/KMS/networking, Google auth, deployment rollback, backup, and restore.
4. Supply chain: pinned dependencies/images, SBOM, license policy, scanning,
   signing, provenance, reproducible builds, and Apache 2.0 self-host parity.
5. Automated parser/retrieval/citation/learning/MCP/security/lifecycle benchmarks
   with frozen fixtures, hashes, trend reporting, and hard release thresholds.
6. Complete fast gate, hosted configuration validation, deletion/restore drill,
   then exactly one successful `make selfhost-smoke` Checkpoint B with Tex and
   telemetry disabled.

Exit result:

- backend contracts and failure behavior are frozen for frontend consumption;
- hosted and self-host deployments preserve the same product invariants;
- the second full smoke is green and frontend work may be proposed to Tauqueer.

### Wave 9 — Technical Phase 12: frontend foundation

Goal: build the typed, accessible, responsive product shell over verified backend
contracts only.

Documentation map: complete FSD global/auth/onboarding/navigation/state/PWA
requirements, frontend TRD contracts, ADR-0013, security cache/session rules, and
accessibility/browser evaluation gates.

Micro-phases:

1. Next.js architecture, generated API client, request/error wrapper, session/
   CSRF handling, correlation IDs, cache policy, and test harness.
2. Hosted Google and self-host OIDC presentation, 18+ confirmation, onboarding,
   logout, expiry, recent auth, unauthorized and recovery flows.
3. Accessible design tokens/components, responsive shell, keyboard/focus model,
   screen-reader landmarks, navigation, global jobs, banners, and error states.
4. PWA manifest/service worker, encrypted account-partitioned offline storage,
   opt-in pinning, logout clearing, update/recovery, and constrained offline seam.
5. Fast frontend gate: generated-contract freshness, component/a11y tests,
   route smoke, responsive viewports, cache isolation, build, and docs. No full
   self-host smoke unless frontend changes a smoke-owned service seam.

### Wave 10 — Technical Phases 13–15: complete UI and beta readiness

Goal: deliver General Memory, Learning, integrations, lifecycle, offline, and
release acceptance as one final product wave.

Micro-phases:

1. Today, Library, Spaces, Private Spaces, sources, uploads, processing,
   reprocess, history, citations, and global jobs.
2. Tiptap editor, MemdotDocument, autosave, revision history, stale-base
   conflict, recovery, AI patch review, and proposal approval.
3. Ask/search/context receipts, source conflicts, historical mode, Memory,
   proposals, activity, external-knowledge labels, and degraded retrieval.
4. Learning setup, syllabus, concepts, coverage, Test, results, confidence,
   Review, Evidence Twin, due reasons, sealed answers, and offline replay.
5. MCP consent/revocation, Notion sync/conflicts, providers/BYOK, settings,
   export, deletion, account recovery, and privacy surfaces.
6. Accessibility/responsive/browser/PWA completion across every route and state.
7. End-to-end FSD acceptance, adversarial security, benchmarks, live authorized
   integration compatibility, restore/incident rehearsal, legal/license docs,
   founder QA, and explicit launch decision.

Exit result:

- every required route/state and `FSD-AC-*` scenario has evidence;
- zero private/cross-account leakage and no deletion resurrection;
- release thresholds, accessibility, self-host parity, and founder QA pass;
- Tauqueer alone decides beta launch.

## 7. Chat report contract

Grok's end-of-wave chat report must be concise but auditable:

1. wave/technical phases, branch, baseline commit, HEAD, and initial/final status;
2. micro-phase completion table and explicit non-goals;
3. requirements/ADRs implemented;
4. changed files grouped by ownership;
5. migrations, contracts, events, compatibility, and data effects;
6. validation table with exact commands, exit results, counts, and skipped tests;
7. security/privacy/failure-mode impact;
8. known limitations and blockers;
9. `git status --short`, `git diff --stat`, `git diff --check` result;
10. confirmation of no unauthorized commit/push/deploy/external mutation.

Raw logs, patches, and inventories should be placed in `/tmp` only when Codex
needs them. Codex normally inspects the working tree directly.

## 8. Current execution pointer

- Accepted waves: 1, 2, and 3.
- Next eligible wave: Wave 4 covering technical Phases 4–5.
- Active wave: none until Tauqueer authorizes the Wave 4 prompt.
- Full smoke checkpoints: Wave 6 after Phase 8, and Wave 8 after Phase 11.
- Frontend begins only in Wave 9 after Checkpoint B and owner authorization.
- Phase prompts, correction prompts, and reports are delivered in chat only.
