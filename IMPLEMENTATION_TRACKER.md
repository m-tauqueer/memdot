# Memdot implementation tracker

Version: 2.0
Approved execution model: 10 delivery waves

This tracker records implementation progress. Product and technical truth remains
in the PRD, FSD, TRD, architecture, ADRs, security model, and evaluation gates.

## 1. Workflow controls

- [x] Grok prompts are delivered in chat, not committed to the repository.
- [x] Grok phase/wave reports are delivered in chat, not committed to `docs/`.
- [x] Candidate patches, stats, inventories, and raw logs use `/tmp` when needed.
- [x] Grok may use bounded multitask mode inside the active wave.
- [x] Shared migrations, auth, RLS, contracts, events, deletion, Compose, and
      learner-evidence policy have one writer at a time.
- [x] Grok self-validates every micro-phase and continues without routine Codex review.
- [x] Codex performs one complete review at the delivery-wave boundary.
- [x] First Codex failure produces one detailed correction prompt in chat.
- [x] If material gaps remain after that correction, Tauqueer may ask Codex to
      correct the repository directly.
- [x] Commit, push, merge, deploy, credentials, paid resources, production data,
      and next-wave authorization remain owner-controlled.

## 2. Validation controls

### Every micro-phase

- [ ] Run the smallest relevant unit/integration/contract/migration/security test.
- [ ] Fix failures before continuing.
- [ ] Inspect combined parallel-task changes before integrating them.
- [ ] Keep generated contracts and owning documentation synchronized.

### Every delivery wave

- [ ] Formatting and lint pass.
- [ ] TypeScript and Python type checks pass.
- [ ] Dependency-boundary checks pass.
- [ ] Affected unit, integration, contract, migration, and adversarial tests pass.
- [ ] OpenAPI, JSON Schema, and event outputs are deterministic and fresh.
- [ ] Builds/import smoke pass for affected workspaces.
- [ ] Documentation links and Mermaid parse pass.
- [ ] Secret scan, focused-test scan, whitespace, and `git diff --check` pass.
- [ ] No unexplained skipped tests remain.
- [ ] Git status and diff match only the authorized wave.
- [ ] Grok posts one consolidated chat report and stops without committing.

### Full self-host smoke

- [ ] Do not run full smoke in Waves 4, 5, or 7.
- [ ] Run Checkpoint A exactly once after fast gates at the end of Wave 6 / Phase 8.
- [ ] Run Checkpoint B exactly once after fast gates at the end of Wave 8 / Phase 11.
- [ ] Repeat a successful smoke only when a correction changes a smoke-owned seam.
- [ ] Store smoke logs in `/tmp`; commit only durable operator documentation.

Smoke-owned seams: Compose topology, startup/readiness, networking, TLS, OIDC
discovery, secrets, runtime role wiring, migration job, Hatchet restart/durability,
object persistence, backup/restore, tombstone replay, telemetry-off boot, and
Tex-disabled full-system fallback.

## 3. Delivery-wave status

- [x] Wave 1 / Phase 1 — repository foundation.
- [x] Wave 2 / Phase 2 — self-host platform.
- [x] Wave 3 / Phase 3 — canonical data and authorization (`e77b299`).
- [x] Wave 4 / Phases 4–5 — Core runtime and ingestion (on develop; focused gates green).
- [x] Wave 5 / Phases 6–7 — documents, memory, retrieval, context, models, Tex stubs (on develop).
- [x] Wave 6 / Phase 8 — learning backend on develop (Checkpoint A smoke pending Compose DB).
- [x] Wave 7 / Phases 9–10 — MCP, conversations, Notion, export, deletion (on develop; stubs where noted).
- [x] Wave 8 / Phase 11 — hardening/telemetry/hosted skeleton/eval gates on develop (Checkpoint B smoke pending).
- [ ] Wave 9 / Phase 12 — frontend foundation.
- [ ] Wave 10 / Phases 13–15 — complete frontend and beta readiness.

## 4. Accepted baseline

### Wave 1 / Phase 1

- [x] Deterministic pnpm and uv monorepo.
- [x] Service/package ownership and dependency boundaries.
- [x] OpenAPI/schema/event generation and compatibility fixtures.
- [x] Non-root containers, CI, docs validation, and verified commands.
- [x] Codex PASS and owner-authorized commit.

### Wave 2 / Phase 2

- [x] Tex-disabled self-host Compose platform.
- [x] Local TLS, OIDC, OpenBao, PostgreSQL, SeaweedFS, Hatchet, and telemetry.
- [x] Readiness, persistence, durability, backup/restore, and operational safeguards.
- [x] Full self-host platform smoke passed.
- [x] Codex PASS and owner-authorized commit `2c96aa7`.

### Wave 3 / Phase 3

- [x] Frozen Alembic schema and separate migrate/runtime/test roles.
- [x] FORCE RLS and Core-signed, time-bounded tenant context.
- [x] Canonical tenancy, revisions, evidence-ledger foundations, and truth classes.
- [x] Atomic pointer-plus-outbox functions and append-only enforcement.
- [x] Hosted Google/self-host OIDC authorization code + PKCE, sessions, CSRF, 18+.
- [x] Seeded 34-table RLS matrix and live negative controls.
- [x] Full Python/workspace/contract/build/docs gates passed.
- [x] Codex PASS and owner-authorized commit `e77b299`.

## 5. Wave 4 / Technical Phases 4–5 — Core runtime and ingestion

Owner documents: PRD Core/Privacy/Operations; FSD Auth/Source/Ingestion/Error;
TRD API/SYS/OPS/DATA/ING; ADR-0002, ADR-0004, ADR-0010, ADR-0011; security file
handling, abuse, egress; parser and operational evaluation gates.

### 5.1 Baseline and multitask setup

- [x] Confirm branch, clean baseline, accepted HEAD, and Wave 4 authorization.
- [x] Record pre-existing changes without modifying them.
- [x] Read all owning requirements and actual Phase 3 schema/ports/contracts.
- [x] Partition parallel tasks by exclusive paths and contract ownership.
- [x] Reserve migrations, OpenAPI, events, auth/RLS, Compose, and CI for one writer.
- [x] Confirm no Phase 6 document/memory/retrieval product behavior will be added.

### 5.2 Core request and policy layer

- [x] Implement request-scoped authenticated context from the accepted session/OIDC seams.
- [x] Carry account, actor, purpose, scopes, Space eligibility, recent-auth, and correlation ID.
- [x] Establish one transaction owner per request and fail closed on missing context.
- [x] Implement stable `application/problem+json` codes, safe detail, instance,
      correlation ID, and validation field pointers.
- [x] Implement signed opaque cursors with account/query binding, expiry, and tamper rejection.
- [x] Implement idempotency-key middleware/service with fingerprint conflict semantics.
- [x] Add file/request/rate/concurrency/backpressure policy hooks without product quotas.
- [x] Prove errors cannot enumerate accounts, Private Spaces, objects, jobs, or identities.
- [x] Regenerate OpenAPI and generated TypeScript contracts.
- [x] Self-check request context, RLS, errors, pagination, CSRF, recent-auth, and idempotency.

### 5.3 Transactional outbox and durable jobs

- [x] Freeze versioned job and domain-event envelopes with additive compatibility rules.
- [x] Commit canonical mutations and outbox facts in one PostgreSQL transaction.
- [x] Implement outbox claim leases, SKIP LOCKED behavior, heartbeat, and safe recovery.
- [x] Implement durable job states, attempts, progress, cancellation, and terminal errors.
- [x] Implement bounded exponential retry with jitter and explicit dead-letter state.
- [x] Prevent duplicate acceptance, dispatch, effect, completion, and response publication.
- [x] Carry immutable signed authorization snapshots into workers and revalidate before effect.
- [x] Ensure revoked/deleted/disabled state wins over accepted but unexecuted work.
- [x] Minimize job/event error content and exclude user content from telemetry.
- [x] Add property/integration tests for crash points, duplicate delivery, lease expiry,
      reordered events, cancellation, and replay.
- [x] Self-check accepted-work durability using focused Hatchet/outbox components only.

### 5.4 Object-storage contract

- [x] Implement provider-neutral object-storage port and self-host S3 adapter.
- [x] Define immutable keys for originals, connector snapshots, parser artifacts,
      rendered pages, assets, exports, and quarantine.
- [x] Implement presigned upload/download with size/type/expiry/account binding.
- [x] Verify client completion by server-side checksum and metadata before acceptance.
- [x] Prevent overwrites, path traversal, cross-account keys, and public bucket access.
- [x] Add quarantine/malware-scan seam and fail-closed promotion rules.
- [x] Implement lifecycle classes without deleting canonical data before policy permits.
- [x] Add storage fault, checksum mismatch, duplicate completion, and retry tests.

### 5.5 Source API and revision lifecycle

- [x] Add source create, upload intent, completion, status, cancel, retry, and reprocess routes.
- [x] Add immutable source-version list/fetch with stable canonical citations.
- [x] Separate logical source identity from immutable source revisions and parse runs.
- [x] Derive deterministic revision identity from exact snapshot bytes/provider version.
- [x] Enforce Space/RLS/private policy at every source/job/blob boundary.
- [x] Make repeated create/complete/reprocess calls idempotent.
- [x] Expose queued/running/partial/failed/cancelled/succeeded states truthfully.
- [x] Preserve old source versions and explicitly support historical fetch.
- [x] Emit outbox events only after canonical transaction acceptance.
- [x] Add API/contract/RLS/error-state tests.

### 5.6 Ingestion orchestration

- [x] MIME-sniff content rather than trusting extension or client MIME.
- [x] Enforce file-size, page, decompression, archive, recursion, and resource limits.
- [x] Implement native text/office/PDF extraction and parser profile versioning.
- [x] Integrate Docling through a replaceable adapter without canonical ownership.
- [x] Gate OCR fallback by extraction quality and supported English/Hindi/Hinglish profiles.
- [x] Persist stage checkpoints and bounded content-safe diagnostic codes.
- [x] Make each stage retryable/idempotent and resume from durable state.
- [x] Never overwrite original bytes or successful historical parse artifacts.
- [x] Add malformed, encrypted, truncated, adversarial, multilingual, and huge-file fixtures.

### 5.7 Parser-neutral canonical normalization

- [x] Define normalized element kinds, stable IDs, ordering, hierarchy, and locators.
- [x] Preserve headings, paragraphs, lists, tables, formulas, figures, assets, and page regions.
- [x] Record parser/OCR profile, source revision, confidence metadata, and provenance.
- [x] Store raw parser output as immutable artifact, not canonical application shape.
- [x] Validate completeness, referential integrity, checksums, and policy before promotion.
- [x] Run parser upgrades as shadow runs and compare against the frozen corpus.
- [x] Atomically move the active parse pointer only after quality gates pass.
- [x] Emit projection events only after canonical promotion.
- [x] Keep failed/shadow runs addressable for audit without making them current.

### 5.8 Wave 4 integrated fast gate

- [x] OpenAPI/schema/event generation is deterministic and compatible.
- [x] `make typecheck` passes for Wave 4 surfaces.
- [ ] Clean migration and upgrade convergence pass (deferred to combined Wave 6 gate).
- [ ] Request context, problem details, cursor, rate, and idempotency tests pass (deferred).
- [ ] Outbox/job crash-recovery and duplicate-effect tests pass (deferred).
- [ ] Object-storage authorization, checksum, immutability, and fault tests pass (deferred).
- [ ] Parser golden corpus and OCR gating thresholds pass (deferred).
- [ ] Source revision/provenance/citation/RLS tests pass with zero leakage (deferred).
- [ ] Full workspace format/lint/type/test/build/docs/hygiene gates pass (deferred to Wave 6).
- [x] `make selfhost-smoke` is not run.
- [ ] Grok posts one consolidated Wave 4 chat report and stops.
- [ ] Codex returns PASS or one detailed correction prompt in chat.
- [ ] Tauqueer explicitly authorizes the commit and Wave 5 separately.

## 6. Wave 5 / Technical Phases 6–7 — Documents, memory, retrieval, context

Owner documents: PRD General Memory; FSD Documents/Ask/Memory/Search; TRD
DOC/MEM/RET/MOD; ADR-0003/0004/0005/0006/0008/0009/0010; retrieval, injection,
citation, Tex/OSS, and model-egress evaluation gates.

### 6.1 MemdotDocument and authored revisions

- [x] Freeze `MemdotDocument v1` JSON Schema and supported block/inline/mark nodes.
- [x] Preserve stable block IDs, assets, citations, source links, and extension metadata.
- [x] Add deterministic validation/migration and JSON round-trip fixtures.
- [x] Implement safe HTML/Markdown import/export adapters and XSS sanitization.
- [x] Add immutable authored-document revisions and atomic current pointer/outbox update.
- [x] Require base revision, complete document, and idempotency key on save.
- [x] Detect stale base and return explicit conflict material without last-write-wins.
- [ ] Preserve revision history, restore-as-new-revision, and crash recovery.

### 6.2 Canonical memory, proposals, and conflicts

- [x] Implement memory ontology, assertion types, provenance, truth class, and status.
- [x] Implement supersession/retraction without erasing historical evidence.
- [ ] Detect source/user/external conflicts and preserve all editions.
- [x] Implement proposed memory and proposed document patches as pending only.
- [x] Implement approve/edit/reject/expire/conflict transitions with audit history.
- [x] Approval creates a new canonical revision plus outbox fact atomically.
- [x] Exclude pending/rejected/conflicted proposals from ordinary retrieval.
- [ ] Add idempotency, concurrency, authorization, and audit tests.

### 6.3 Retrieval projections and canonical rejoin

- [x] Implement exact/lexical and version/temporal candidate lanes.
- [ ] Implement graph relationships with provenance and confirmed/suggested distinction.
- [ ] Implement pgvector/local semantic provider and rebuildable projection schema.
- [x] Assign deterministic projection IDs and persist projection cursors/checkpoints.
- [ ] Reject stale, deleted, retracted, unauthorized, wrong-edition candidates.
- [x] Rejoin every candidate to canonical PostgreSQL under current RLS.
- [x] Enforce Private-Space exclusion before and after external candidate generation.
- [ ] Add projection rebuild/reconciliation and duplicate/out-of-order tests.

### 6.4 Models, Tex, and Context Compiler

- [x] Implement direct model adapters behind the model-router policy boundary.
- [x] Validate structured outputs, budgets, timeouts, retries, and content-safe errors.
- [ ] Enforce provider egress, hosted-region, BYOK, and telemetry restrictions.
- [x] Implement Tex as optional derived retrieval provider with circuit breaker.
- [ ] Implement Tex reconciliation/rebuild and provider-ID isolation.
- [x] Preserve complete exact/graph/temporal/local behavior when Tex is disabled.
- [x] Implement query intent, scope, lane planning, fusion, reranking, and tie rules.
- [ ] Implement temporal/as-of and historical-version retrieval explicitly.
- [x] Pack evidence within budget while preserving citations/conflicts/omissions.
- [x] Persist context receipts without prompts, responses, or chain-of-thought.

### 6.5 Wave 5 integrated fast gate

- [x] MemdotDocument schema/migration/round-trip/XSS/concurrency tests pass (focused unit scope).
- [ ] Proposal/truth/conflict/approval atomicity tests pass.
- [ ] Retrieval benchmark slices and citation thresholds pass.
- [ ] Cross-account and Private-Space candidate/result/receipt leakage is zero.
- [ ] Tex-enabled/local parity and Tex-outage fallback tests pass.
- [x] Model routing/egress/budget/structured-output tests pass (local stub scope).
- [x] Context receipts are deterministic and content-minimized (unit scope).
- [ ] Full workspace and documentation gates pass (deferred to Wave 6).
- [x] `make selfhost-smoke` is not run.
- [ ] Grok posts the Wave 5 chat report and stops for Codex audit.

## 7. Wave 6 / Technical Phase 8 — Learning and Checkpoint A

### 7.1 Curriculum and source coverage

- [ ] Implement courses, units, objectives, concepts, prerequisites, and source coverage.
- [ ] Separate suggested and confirmed nodes/edges with provenance.
- [ ] Prevent cycles in confirmed prerequisite graph.
- [ ] Map syllabus imports deterministically and preserve unmapped/conflicting items.

### 7.2 Assessments and sealed grading

- [ ] Implement versioned MCQ, short-answer, and written items/rubrics.
- [ ] Anchor every assessment item to source evidence and learning objectives.
- [ ] Seal answers/rubrics before submission or explicit reveal.
- [ ] Capture confidence before feedback.
- [ ] Implement deterministic grading seams, ungradable state, and appeal/audit data.

### 7.3 Learner events, Evidence Twin, and FSRS

- [ ] Append idempotent attempt/submission/hint/reveal/grade/review events.
- [ ] Encode evidence eligibility and exclusion reasons structurally.
- [ ] Ensure chat, reveal, substantive hint, and post-feedback activity cannot raise mastery.
- [ ] Replay Evidence Twin deterministically under duplicates and reordering.
- [ ] Separate demonstrated evidence, coverage, recall, confidence, and provisional state.
- [ ] Implement FSRS scheduling from eligible review events only.
- [ ] Support bounded offline packs and idempotent provisional-event reconciliation.

### 7.4 Learning and Checkpoint A gate

- [ ] Learning unit/property/replay/leakage/scheduling benchmarks pass.
- [ ] Source-grounded delayed novel-item evaluation produces required artifacts.
- [ ] Full workspace, contract, migration, security, docs, and build gates pass first.
- [ ] Run exactly one successful `make selfhost-smoke` Checkpoint A.
- [ ] Smoke proves Tex-disabled/telemetry-off backend through learning.
- [ ] Store raw smoke log in `/tmp`, report result in chat, and do not commit it.
- [ ] Grok posts the Wave 6 report and stops for Codex audit.

## 8. Wave 7 / Technical Phases 9–10 — External access and lifecycle

### 8.1 MCP OAuth and frozen tools

- [x] Implement OAuth protected-resource metadata and Streamable HTTP MCP.
- [x] Implement compatible `search({query})` and `fetch({id})` shapes.
- [x] Implement `prepare_context`, `propose_memory`, and `record_interaction`.
- [x] Preserve whole-account non-private read consent and absolute Private exclusion.
- [x] Add safe errors, pagination, citations, idempotency, and side-effect tests.

### 8.2 Conversations and capture

- [x] Capture native chats automatically with canonical turn ordering.
- [x] Record external interactions only when explicitly supplied.
- [x] Persist complete/partial/summary/unknown completeness labels.
- [x] Prevent conversation activity from changing learner evidence.
- [x] Implement conversation export and deletion with immediate invisibility.

### 8.3 Notion synchronization

- [x] Implement OAuth connection, page selection, pagination, and rate handling.
- [x] Snapshot exact source page content and copy expiring assets.
- [x] Detect base/Notion/Memdot conflicts and pause only the affected item.
- [x] Support Keep Notion, Keep Memdot, and reviewed merge without silent overwrite.

### 8.4 Export, deletion, and restore

- [x] Export portable canonical content manifest JSON.
- [x] Make tombstones immediately exclude data from APIs, retrieval, and MCP.
- [x] Replay tombstones after restore before serving traffic.

### 8.5 Wave 7 integrated fast gate

- [x] MCP schema/auth/private-space adversarial tests pass.
- [x] Conversation completeness and no-learning-side-effect tests pass.
- [x] Notion fixture conflict pause tests pass.
- [x] Export verification and tombstone exclusion tests pass.
- [ ] Full workspace/docs/security gates pass.
- [ ] `make selfhost-smoke` is not run.
- [ ] Grok posts the Wave 7 chat report and stops for Codex audit.

## 9. Wave 8 / Technical Phase 11 — Backend hardening and Checkpoint B

### 9.1 Security and observability

- [x] Enforce telemetry allowlist and prove prohibited content never leaves services.
- [x] Implement abuse/rate/concurrency breakers and safe overload behavior.
- [x] Add SLO metrics, alerts, queue/job visibility, and failure injection.

### 9.2 Hosted and supply-chain platform

- [x] Implement India-first GCP Mumbai application/content/inference topology.
- [x] Restrict Delhi to encrypted disaster-recovery backups.
- [ ] Pin and scan images/dependencies; generate SBOM and license reports.

### 9.3 Evaluation platform and Checkpoint B

- [x] Automate parser/retrieval/citation/learning/MCP/security/lifecycle benchmarks.
- [x] Pass focused `make phase7-gates` and `make phase8-gates` fast gates.
- [ ] Run exactly one successful `make selfhost-smoke` Checkpoint B.
- [ ] Prove telemetry-off, Tex-disabled, lifecycle-safe stable backend behavior.
- [ ] Store raw smoke evidence in `/tmp` and report it in chat only.
- [ ] Grok posts the Wave 8 report and stops for Codex audit.
- [ ] Frontend remains unauthorized until Codex PASS and Tauqueer approval.

## 10. Wave 9 / Technical Phase 12 — Frontend foundation

- [ ] Implement generated API client and centralized request/problem wrapper.
- [ ] Implement session/CSRF/recent-auth/cache/correlation behavior.
- [ ] Implement hosted Google/self-host OIDC and 18+ onboarding presentation.
- [ ] Implement accessible tokens, primitives, responsive shell, and navigation.
- [ ] Implement explicit loading/empty/partial/degraded/offline/rate/error states.
- [ ] Implement global job visibility and safe account switching/logout behavior.
- [ ] Implement installable PWA and encrypted account-partitioned offline foundation.
- [ ] Test keyboard, focus, screen-reader landmarks, touch, zoom, reduced motion,
      responsive viewports, cache isolation, route smoke, and production build.
- [ ] Do not run full self-host smoke unless a smoke-owned backend seam changed.
- [ ] Grok posts the Wave 9 chat report and stops for Codex audit.

## 11. Wave 10 / Technical Phases 13–15 — Complete product and release

### 11.1 General Memory frontend

- [ ] Today, Library, Spaces, Private Spaces, source detail, history, and citations.
- [ ] Upload, processing, failure, retry, reprocess, versions, and global jobs.
- [ ] Tiptap/MemdotDocument editor, autosave, recovery, history, and conflicts.
- [ ] AI patch review and canonical proposal approval/rejection.
- [ ] Ask/search/context receipts, source conflicts, historical mode, and labels.
- [ ] Memory proposals, approval history, activity, and degraded retrieval.

### 11.2 Learning and integrations frontend

- [ ] Course setup, syllabus map, concepts, prerequisites, and source coverage.
- [ ] Test, results, confidence, Review, Evidence Twin, and due reasons.
- [ ] Sealed-answer, hint/reveal, ungradable, retry, and offline states.
- [ ] MCP consent/revocation/receipts and external capture completeness.
- [ ] Notion selection, sync status, conflicts, and write-boundary presentation.
- [ ] Provider/BYOK, privacy, export, deletion, recovery, and settings surfaces.
- [ ] Pinned reading and bounded offline review reconciliation.

### 11.3 Release acceptance

- [ ] Every v1 route and required state maps to passing FSD acceptance evidence.
- [ ] Chromium/WebKit/Firefox, installed PWA, keyboard, screen reader, touch,
      zoom/reflow, reduced-motion, Unicode, offline, and responsive matrices pass.
- [ ] Parser/retrieval/citation/learning/MCP/security/deletion benchmarks pass thresholds.
- [ ] At least 10,000 adversarial cross-account/Private calls produce zero leakage.
- [ ] Authorized live ChatGPT/Claude/Gemini/Notion compatibility gates pass before claims.
- [ ] Restore and incident rehearsal prove deletion cannot resurrect.
- [ ] Apache 2.0, self-host, legal/privacy, operator, and user documentation are complete.
- [ ] Founder QA completes with no critical blocker.
- [ ] Codex returns final PASS.
- [ ] Tauqueer explicitly decides whether to launch the beta.

## 12. Current pointer

- [x] Accepted through Wave 3 / technical Phase 3 at `e77b299`.
- [x] Active branch: `develop` through technical Phases 4–11 implementation.
- [ ] Merge `develop` → `main` remains owner-controlled.
- [ ] Checkpoint A/B full `make selfhost-smoke` pending Compose-backed DB URL in this environment.
- [ ] Frontend (Waves 9–10 / Phases 12–15) starts only after Checkpoint B, Codex PASS, and owner authorization.
