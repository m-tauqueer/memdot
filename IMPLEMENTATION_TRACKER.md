# Memdot Implementation Tracker

Version: 1.1
Execution model: Tauqueer owns decisions; Grok completes and self-validates one macro-phase; Codex audits at the phase boundary
Architecture baseline: 2026-07-15 founding documentation

## 1. Governing execution rules

- [ ] Treat docs/README.md, the PRD, FSD, TRD, System Architecture, accepted ADRs, Security and Privacy Threat Model, Evaluation and Release Gates, Codebase Context Map, AGENTS.md, and this tracker as the implementation baseline.
- [ ] Never describe a documented target as implemented until the corresponding code, migration, test, and runtime evidence exist.
- [ ] Execute one owner-approved macro-phase at a time. Its numbered micro-phases are Grok's internal implementation and self-validation sequence.
- [ ] After a micro-phase self-check passes, Grok continues to the next micro-phase in the same macro-phase without waiting for Codex.
- [ ] If a micro-phase self-check fails, Grok fixes and reruns it before continuing. If an architectural contradiction, owner decision, credential, paid resource, or unsafe external action is required, Grok stops and reports the blocker.
- [ ] Grok submits one consolidated report only after all micro-phases and the macro-phase exit gate pass.
- [ ] If Codex returns FAIL at the macro-phase audit, keep that macro-phase open, apply the requested corrections, rerun affected and phase-level gates, and resubmit one consolidated report.
- [ ] Grok must not commit, push, merge, deploy, rotate credentials, create paid resources, or alter production data without Tauqueer's explicit instruction.
- [ ] Never weaken a PRD, FSD, TRD, ADR, privacy, or evaluation requirement to make a test pass. Escalate genuine contradictions to Codex.
- [ ] Keep PostgreSQL and immutable object storage canonical. Tex, pgvector indexes, caches, projections, and model outputs remain rebuildable or proposed.
- [ ] Keep Private Spaces outside every external-AI candidate set, result, receipt, error, cache, and interaction target.
- [ ] Keep AI-authored facts, memories, graph changes, and document edits pending until first-party user approval.
- [ ] Keep learner evidence append-only and derived only from eligible assessment events; conversations and interaction capture never establish demonstrated learning.
- [ ] Preserve complete Tex-disabled, telemetry-off self-host functionality throughout development.
- [ ] Update documentation, generated contracts, Codebase Context Map, and verified commands in the same micro-phase that changes them.
- [ ] Use only synthetic, openly licensed, or explicitly authorized content in tests. Never place real credentials or personal content in fixtures, logs, screenshots, or handoffs.

## 2. Mandatory Grok phase protocol

### 2.1 Before coding

- [ ] Confirm the owner-approved macro-phase, its complete micro-phase order, and its final stop boundary.
- [ ] Report the current branch, base commit, git status --short, and pre-existing uncommitted files.
- [ ] Read AGENTS.md and IMPLEMENTATION_TRACKER.md.
- [ ] Read the owning PRD, FSD, TRD requirements, ADRs, threat controls, and evaluation gates named by the micro-phase.
- [ ] Inspect the actual repository; do not assume a path, command, dependency, or migration exists because the target map names it.
- [ ] List the exact requirement IDs being implemented and the invariants that could be affected.
- [ ] State any discovered decision or blocker before expanding scope.

### 2.2 While coding

- [ ] Change only files required by the micro-phase.
- [ ] Add or update tests with the behavior; never postpone required tests to a later phase unless this tracker explicitly says so.
- [ ] Generate contracts from their canonical owner rather than maintaining duplicate TypeScript and Python schemas.
- [ ] Use migrations for database changes and safe expand, migrate, contract sequencing for compatibility changes.
- [ ] Keep logs and test output content-free and secret-free.
- [ ] Preserve unrelated user changes and pre-existing dirty files.
- [ ] Update requirement traceability and current-path documentation when ownership, paths, commands, interfaces, or behavior change.

### 2.3 Internal micro-phase checkpoint

- [ ] Run every validation assigned to the micro-phase and fix failures before continuing.
- [ ] Record the micro-phase requirement IDs, files changed, commands, raw results, migrations/contracts, and known limitations in working notes for the final phase report.
- [ ] Confirm the change has not weakened canonical ownership, dependency direction, authorization, Private-Space exclusion, proposed-write rules, learner evidence, deletion, telemetry, or self-host parity.
- [ ] Continue to the next micro-phase only when the self-check passes.
- [ ] Do not ask Codex for routine review between micro-phases.
- [ ] Do not commit, push, merge, deploy, create paid resources, or mutate production/external data between micro-phases without Tauqueer's explicit authorization.

### 2.4 Required phase-end Grok handoff to Codex

- [ ] Stop implementation after every micro-phase and the complete macro-phase exit gate pass, or immediately when a defined blocker is reached.
- [ ] Provide heading: GROK PHASE REPORT — PHASE X.
- [ ] Provide scope completed and explicit non-goals.
- [ ] Provide exact PRD, FSD, TRD, ADR, security, and EVAL IDs covered.
- [ ] Provide a micro-phase-by-micro-phase self-check summary.
- [ ] Provide every changed, created, generated, renamed, and deleted file grouped by purpose.
- [ ] Provide migrations, schema versions, event versions, public API changes, and compatibility effect.
- [ ] Provide commands executed and unedited terminal results, including failures and reruns.
- [ ] Provide test counts, skipped tests, expected failures, coverage changes, benchmark fixture/version, and performance measurements where applicable.
- [ ] Provide git status --short, git diff --stat, and git diff --check.
- [ ] Provide the complete diff or an owner-shareable patch; do not omit generated or migration files.
- [ ] Provide security and privacy impact, including tenancy, Private Spaces, secrets, telemetry, deletion, and provider egress.
- [ ] Provide phase exit-gate results, known limitations, follow-ups, and blockers without claiming later phases are complete.
- [ ] Confirm that no commit, push, merge, deploy, or external resource mutation was performed unless Tauqueer explicitly authorized it.

### 2.5 Codex phase audit contract

- [ ] Codex verifies scope and repository state before accepting test claims.
- [ ] Codex traces the diff to the named requirements and ADRs.
- [ ] Codex checks dependency direction, canonical ownership, migrations, idempotency, authorization, privacy, failure behavior, and docs.
- [ ] Codex checks raw validation evidence and may request targeted commands or additional diffs.
- [ ] Codex returns exactly one verdict: PASS, FAIL — CORRECTIONS REQUIRED, or BLOCKED — OWNER DECISION REQUIRED.
- [ ] Only a macro-phase PASS makes its changes eligible for an owner-authorized commit and the next phase eligible to start.
- [ ] Macro-phase completion requires evidence that every contained micro-phase self-check and the macro exit gate passed.

## 3. Macro-phase sequence

- [x] Phase 1 — Repository foundation and production-grade monorepo structure
- [x] Phase 2 — Self-host infrastructure and local developer platform
- [ ] Phase 3 — Canonical PostgreSQL ledger, tenancy, identity, and authorization
- [ ] Phase 4 — Core API, durable transactions, workflows, and object storage
- [ ] Phase 5 — Source ingestion, parsing, OCR, normalization, and reprocessing
- [ ] Phase 6 — Rich documents, canonical memory, conflicts, and proposed writes
- [ ] Phase 7 — Retrieval, Context Compiler, model routing, Tex, and OSS fallback
- [ ] Phase 8 — Learning backend, Evidence Twin, assessment, and FSRS
- [ ] Phase 9 — MCP, OAuth, external AI, conversations, and capture
- [ ] Phase 10 — Notion synchronization, export, deletion, and restore safety
- [ ] Phase 11 — Security hardening, observability, deployment, and evaluation platform
- [ ] Phase 12 — Frontend foundation, authentication, responsive shell, and PWA base
- [ ] Phase 13 — Frontend General Memory, editor, ingestion, Ask, and Memory
- [ ] Phase 14 — Frontend Learning, integrations, settings, offline, and accessibility
- [ ] Phase 15 — Release candidate, full-system acceptance, and beta launch readiness

# Phase 1 — Repository foundation and production-grade monorepo structure

Primary contracts: TRD-SYS-001..010, TRD-DEP-006..008, ADR-0011, Codebase Context Map sections 2, 3, 11, and 12.

## Micro-phase 1.1 — Repository and workspace scaffold

- [x] Initialize Git on Tauqueer's selected default branch if it is still absent; do not create the first commit before Codex audit.
- [x] Add the Apache 2.0 LICENSE, repository README, contribution conventions, ownership metadata, editor settings, line-ending rules, and a comprehensive secret-safe gitignore.
- [x] Create the target monorepo boundaries: apps/web, apps/mcp, services/core, services/workers, services/model-router, packages/contracts, packages/domain-python, packages/ui, infra/compose, infra/hosted, tests/benchmark, and tests/security.
- [x] Pin a deterministic TypeScript and Python toolchain. Default to one pnpm workspace and one uv-managed Python workspace unless an inspected constraint requires a documented change.
- [x] Pin Node, Python, package-manager, Docker, and Compose compatibility in machine-readable files; do not guess unverified commands.
- [x] Add root scripts that delegate to owning workspaces without embedding domain policy.
- [x] Add architecture-boundary documentation explaining which directories may depend on which.
- [x] Add empty package markers only where required; do not implement domain behavior in this batch.
- [x] Validate a clean dependency install from an empty cache.
- [x] Run workspace discovery and prove every intended project is recognized.
- [x] Record the micro-phase self-check in working notes and continue only if it passes.
- [x] Grok self-check: PASS.

## Micro-phase 1.2 — Service and package skeletons

- [x] Scaffold the Next.js TypeScript web application without product screens.
- [x] Scaffold the thin TypeScript MCP application without database, Tex, object-store, or model dependencies.
- [x] Scaffold the FastAPI core service, Python worker service, and isolated model-router service with typed configuration and health endpoints only.
- [x] Scaffold packages/contracts as the generated-contract boundary, packages/domain-python as domain and provider-port ownership, and packages/ui as frontend-only primitives.
- [x] Add multi-stage, non-root, minimal runtime Dockerfiles with explicit health checks for every runtime component.
- [x] Enforce dependency direction with automated import and workspace-boundary checks.
- [x] Prove web and MCP cannot import provider adapters and that workers cannot import UI code.
- [x] Run build, lint, type-check, import, and health-start smoke checks for every skeleton.
- [x] Record the micro-phase self-check in working notes and continue only if it passes.
- [x] Grok self-check: PASS.

## Micro-phase 1.3 — Contract and schema toolchain

- [x] Establish Core-owned OpenAPI generation and TypeScript client generation without hand-written competing DTOs.
- [x] Establish versioned JSON Schema generation for MemdotDocument, public resources, provider ports, and export manifests.
- [x] Establish versioned event schemas with compatibility checks and additive-field policy.
- [x] Establish application/problem+json types and stable error-code registry.
- [x] Add schema formatting, validation, backward-compatibility, and generated-file freshness checks.
- [x] Add fixtures proving equivalent serialization at Python, OpenAPI, generated TypeScript, and event boundaries.
- [x] Run generation twice and prove deterministic zero-diff output.
- [x] Run contract compilation and compatibility checks.
- [x] Record the micro-phase self-check in working notes and continue only if it passes.
- [x] Grok self-check: PASS.

## Micro-phase 1.4 — CI, repository hygiene, and verified commands

- [x] Create CI jobs for formatting, linting, Python typing, TypeScript typing, unit tests, contract compatibility, migration checks, dependency boundaries, documentation links, Mermaid rendering, secret scanning, dependency review, and container builds.
- [x] Configure tests to fail on unexpected skips, focused tests, stale generated files, or committed secrets.
- [x] Add deterministic test-environment conventions and content-safe fixture rules.
- [x] Add root commands for bootstrap, lint, type-check, unit tests, contract tests, documentation validation, Compose validation, and clean rebuild.
- [x] Update AGENTS.md and Codebase Context Map with only commands and paths verified in this phase.
- [x] Record toolchain and command ownership in the repository README.
- [x] Run the complete Phase 1 CI-equivalent suite locally from a clean checkout state.
- [x] Record the micro-phase self-check in working notes and continue only if it passes.
- [x] Grok self-check: PASS.

## Phase 1 exit gate

- [x] A clean machine can install dependencies, discover every workspace, build all skeletons, and run the documented validation commands.
- [x] All dependency-direction violations fail automatically.
- [x] Generated contracts are deterministic and have one canonical owner.
- [x] Containers run as non-root and health checks pass.
- [x] CI-equivalent validation passes with no ignored failures or unexplained warnings.
- [x] AGENTS.md and Codebase Context Map describe actual verified paths and commands.
- [x] No product/domain functionality is falsely claimed.
- [x] Grok submits one consolidated Phase 1 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [x] Codex performs a complete Phase 1 architecture audit and returns PASS.
- [x] Tauqueer explicitly authorizes the Phase 1 commit(s) and start of Phase 2.

# Phase 2 — Self-host infrastructure and local developer platform

Primary contracts: TRD-DEP-004..008, TRD-SEC-005..007, TRD-OPS-009..013, ADR-0011.

## Micro-phase 2.1 — Tex-disabled Compose topology

- [x] Implement the complete self-host Compose topology for Caddy, web, Core API, MCP, workers, model router, Hatchet, PostgreSQL with pgvector, SeaweedFS, Keycloak, OpenBao, OpenTelemetry, and Grafana-compatible observability.
- [x] Keep Tex absent or disabled in the default profile and add it only behind an optional provider profile.
- [x] Define isolated public, application, data, workflow, and observability networks with no unnecessary host exposure.
- [x] Add named persistent volumes, deterministic health checks, startup dependencies based on health rather than sleep, and bounded restart policies.
- [x] Add development overrides without weakening the production-like base topology.
- [x] Validate docker compose config and a fresh Tex-disabled boot.
- [x] Prove every service reaches healthy state and no internal datastore is publicly exposed.
- [x] Record the micro-phase self-check in working notes and continue only if it passes.
- [x] Grok self-check: PASS.

## Micro-phase 2.2 — Configuration, secrets, and local trust

- [x] Implement typed, fail-fast configuration for every service with explicit hosted, self-host, test, and development modes.
- [x] Add safe example environment files containing no usable credentials.
- [x] Integrate OpenBao Transit for self-host secret encryption and define a hosted key-provider interface without adding hosted credentials.
- [x] Configure local TLS through Caddy and document trusted local certificate behavior.
- [x] Configure Keycloak realms and clients as reproducible configuration while leaving product authorization in Core.
- [x] Configure Hatchet, object-store, database, and telemetry credentials through secret references rather than images or source.
- [x] Add startup checks that reject default production secrets, invalid audiences, unsafe origins, and plaintext provider credentials.
- [x] Run secret scanning and configuration-negative tests.
- [x] Record the micro-phase self-check in working notes and continue only if it passes.
- [x] Grok self-check: PASS.

## Micro-phase 2.3 — Infrastructure durability and operational smoke tests

- [x] Add PostgreSQL backup, restore, and migration-job entrypoints that never auto-run destructive migrations during application startup.
- [x] Add immutable-object-store lifecycle and backup smoke tooling.
- [x] Add local service readiness, dependency failure, restart, and persistent-volume verification scripts.
- [x] Add content-free baseline dashboards for health, request failures, queue depth, database availability, object-store availability, and workflow availability.
- [x] Restart database, object storage, workers, and the complete stack during accepted dummy work and verify durable recovery (live smoke 2026-07-16 on local dockerd; Hatchet accepted-work restart proven).
- [x] Restore a disposable backup into a clean stack and verify canonical checksums (live smoke; `memdot_restore_*` only; ops/product DBs rejected).
- [x] Run the complete self-host smoke suite with Tex disabled and telemetry export disabled (`make selfhost-smoke` exit 0; project `memdot-smoke-20260716024239-1851798`).
- [x] Record the micro-phase self-check in working notes and continue only if it passes.
- [x] Grok self-check: PASS (correction round 3).

## Phase 2 exit gate

- [x] A fresh operator can start the complete self-host topology using documented commands and safe example configuration.
- [x] The product skeleton operates without Tex or paid model APIs.
- [x] Internal services and stores are not unintentionally internet-facing.
- [x] Secrets are encrypted or referenced and never logged.
- [x] Restart, volume persistence, backup, and restore smoke tests pass (live smoke evidence).
- [x] Compose, health, configuration-negative, and secret-scan gates pass.
- [x] Grok submits one consolidated Phase 2 report using docs/execution/PHASE_REPORT_TEMPLATE.md (correction round 3).
- [x] Codex performs a complete Phase 2 infrastructure and security audit and returns PASS.
- [x] Tauqueer explicitly authorizes the Phase 2 commit(s) and start of Phase 3.

# Phase 3 — Canonical PostgreSQL ledger, tenancy, identity, and authorization

Primary contracts: TRD-DATA-001..012, TRD-SEC-001, TRD-SEC-013, FSD-AUTH-*, FSD-ONB-*, ADR-0002, ADR-0007.

## Micro-phase 3.1 — Migration framework and tenancy schema

- [ ] Configure SQLAlchemy and Alembic with separate runtime and migration roles.
- [ ] Add UUIDv7 identity generation, immutable created metadata, and deterministic-ID utilities where the TRD requires UUIDv5.
- [ ] Create account, user, account_member, space, space_member, age-attestation, and session/grant foundations.
- [ ] Put account_id on every account-owned row and space_id on every space-owned row.
- [ ] Add composite foreign-key or trigger validation preventing cross-account attachment.
- [ ] Enable and FORCE PostgreSQL RLS on every account-owned table.
- [ ] Add request-scoped app.account_id, app.actor_id, and app.purpose handling with pooled-connection reset.
- [ ] Ensure runtime roles have no BYPASSRLS and cannot disable row security.
- [ ] Run clean migration, repeat migration, schema-diff, and migration-role tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 3.2 — Evidence-ledger foundations

- [ ] Create canonical source, source_revision, blob metadata, authored-document, document_revision, parse-run, element, provenance, truth-class, conflict-set, proposal, conversation, audit, and current-pointer foundations needed by later phases.
- [ ] Separate immutable revisions and events from mutable current pointers.
- [ ] Add canonical outbox_event, idempotency_record, job, job_attempt, and projection-state foundations.
- [ ] Implement truth classes: source assertion, user assertion, external knowledge, derived proposal, approved derived, learner evidence, and system metadata.
- [ ] Preserve conflicts and supersession without deleting historical evidence.
- [ ] Add database constraints for immutable revisions, append-only event tables, and valid current-pointer ownership.
- [ ] Add schema ownership notes mapping each table to Core, workers, or derived providers.
- [ ] Run constraint, immutability, provenance, and cross-account attachment tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 3.3 — Hosted Google authentication and self-host OIDC

- [ ] Implement OIDC validation behind an issuer adapter.
- [ ] Configure hosted mode to accept Google sign-in only through the documented broker.
- [ ] Configure self-host mode for an operator-supplied OIDC issuer and first-operator bootstrap.
- [ ] Require explicit 18+ self-attestation before creating an active hosted content account.
- [ ] Reject a declined or missing attestation without collecting date of birth or identity documents.
- [ ] Implement secure same-site browser sessions, CSRF protection, rotation, logout, recent-auth markers, and revocation.
- [ ] Keep Keycloak authentication claims separate from product permissions and Private-Space rules.
- [ ] Add issuer, audience, expiry, nonce, replay, CSRF, session-fixation, logout, and recent-auth tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 3.4 — RLS and authorization adversarial suite

- [ ] Build reusable account, actor, purpose, Space, Private-Space, and external-client test factories.
- [ ] Test first-party versus external-AI eligibility as separate policies.
- [ ] Prove external clients cannot read, infer, write into, enumerate, or receive errors revealing Private Spaces.
- [ ] Test pooled-connection context reset and malicious transaction-setting attempts.
- [ ] Test every current account-owned table for cross-account reads, writes, foreign-key attachment, pagination, and error leakage.
- [ ] Add CI enforcement requiring new account-owned tables to register RLS and adversarial tests.
- [ ] Run the Phase 3 cross-account matrix with zero leakage.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 3 exit gate

- [ ] Migrations produce the same validated schema on a clean database and an upgraded database.
- [ ] PostgreSQL is the enforceable authorization join point, not merely an application convention.
- [ ] Hosted Google-only authentication, self-host OIDC, 18+ activation, sessions, CSRF, and recent authentication work as specified.
- [ ] Every implemented account-owned table has FORCE RLS and passing adversarial tests.
- [ ] Immutable revisions, append-only events, truth classes, conflicts, and canonical pointers are structurally enforced.
- [ ] No Keycloak, Tex, provider, or UI claim can override product authorization.
- [ ] Grok submits one consolidated Phase 3 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 3 data and authorization audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 3 commit(s) and start of Phase 4.

# Phase 4 — Core API, durable transactions, workflows, and object storage

Primary contracts: TRD-API-001..008, TRD-SYS-002..005, TRD-OPS-004, TRD-OPS-009..010, Codebase Context Map sections 6 and 7.

## Micro-phase 4.1 — Core application and API policy layer

- [ ] Implement FastAPI application boundaries, dependency injection, transaction ownership, and domain-service interfaces.
- [ ] Implement authenticated request context with account, actor, purpose, Space eligibility, scopes, recent-auth, and correlation ID.
- [ ] Implement application/problem+json responses with stable safe codes and field pointers.
- [ ] Implement opaque signed cursor pagination with deterministic sort-value and ID ordering.
- [ ] Implement request and response schema validation, content-type enforcement, request-size controls, and safe error mapping.
- [ ] Implement rate, concurrency, and backpressure interfaces without advertising billing quotas.
- [ ] Add OpenAPI generation as the canonical public contract and regenerate TypeScript clients.
- [ ] Test invalid, unauthorized, partial, degraded, rate-limited, and internal-failure responses for content and existence leakage.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 4.2 — Idempotency, transactional outbox, and durable jobs

- [ ] Implement idempotency-key fingerprinting and atomic original-response replay.
- [ ] Return 409 idempotency_conflict when a key is reused with a different fingerprint.
- [ ] Commit canonical mutations and outbox events in one PostgreSQL transaction.
- [ ] Implement outbox claiming, leases, deduplication, bounded retry with jitter, terminal/dead-letter states, and content-safe attempt history.
- [ ] Integrate Hatchet workflows using signed immutable authorization snapshots containing IDs and hashes rather than content or credentials.
- [ ] Implement monotonic durable job stages with explicit retry attempts under one logical job.
- [ ] Test transaction rollback, process crash after commit, duplicate delivery, out-of-order delivery, lease expiry, poison jobs, and replay convergence.
- [ ] Prove accepted work is never reported successful before durable acceptance.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 4.3 — Immutable object-storage port

- [ ] Implement ObjectStore port operations for immutable put, head, get, delete, signed transfer, generation match, and hash verification.
- [ ] Implement SeaweedFS self-host adapter and a hosted cloud-storage adapter boundary.
- [ ] Store original binaries and parser artifacts under immutable generated keys; never rely on mutable names for identity.
- [ ] Implement presigned upload intents so Core never buffers large file bodies.
- [ ] Verify account ownership, upload expiry, object generation, declared size, detected type, and SHA-256 at completion.
- [ ] Make canonical database promotion fail closed if object verification is unavailable or inconsistent.
- [ ] Test tampered hashes, expired URLs, generation replacement, cross-account object keys, interrupted uploads, retries, and object-store outage.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 4.4 — Service contract and worker integration baseline

- [ ] Generate typed clients used by web, MCP, workers, and model router.
- [ ] Implement worker-to-Core or shared-domain transaction seams without allowing workers to invent user-session authorization.
- [ ] Add versioned committed-fact event names and consumer compatibility behavior.
- [ ] Add end-to-end dummy workflows proving API acceptance, outbox dispatch, worker handling, durable status, and idempotent replay.
- [ ] Add tracing propagation using content-free identifiers only.
- [ ] Run contract, integration, crash-recovery, and generated-client tests across Core and workers.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 4 exit gate

- [ ] Public errors, cursor pagination, idempotency, durable 202 jobs, and generated contracts match TRD-API.
- [ ] Canonical writes and outbox facts are atomic.
- [ ] Worker retries converge and expose terminal states without duplicate canonical effects.
- [ ] Object uploads are direct, immutable, hash-verified, account-bound, and safely retryable.
- [ ] Dependency outages cannot fabricate acceptance or broaden authorization.
- [ ] Integration tests survive injected API and worker termination at every transaction boundary.
- [ ] Grok submits one consolidated Phase 4 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 4 API and durability audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 4 commit(s) and start of Phase 5.

# Phase 5 — Source ingestion, parsing, OCR, normalization, and reprocessing

Primary contracts: TRD-ING-001..018, TRD-DATA-007..012, FSD-ING-*, FSD-SRC-*, ADR-0004, EVAL-ING-001..012.

## Micro-phase 5.1 — Ingestion intent, upload, source, and revision lifecycle

- [ ] Implement POST /api/v1/ingestions, POST /api/v1/ingestions/{id}/complete, and GET /api/v1/ingestions/{id}.
- [ ] Support PDF, images, DOCX, PPTX, Markdown, TXT, paste, rich documents, and connector snapshots through typed ingestion intents.
- [ ] Enforce the documented baseline of 100 MiB per object, 1,000 pages per source, two active parse workflows per account, and a bounded durable queue as safety limits rather than billing quotas.
- [ ] Create deterministic source revisions from source identity and verified snapshot hash; identical content returns the existing revision plus a new observation when appropriate.
- [ ] Preserve originals, language hints, native version, checksums, byte/page count, captured time, and immutable object generation.
- [ ] Implement visible accepted, uploading, queued, processing, partial, ready-with-warnings, ready, failed, and retryable states.
- [ ] Test duplicate completion, refresh, reconnect, worker restart, unsupported input, oversized input, overload, and object-verification failure.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 5.2 — Parser-neutral canonical normalization

- [ ] Implement the DocumentParser port with preflight, parse-profile identity, confidence, raw artifact, normalized output, and deterministic status.
- [ ] Implement native-format extraction and Docling-based parsing without making Docling's internal model canonical.
- [ ] Normalize pages, headings, paragraphs, lists, tables, formulas, code, images, slides, notes, and source locators into parser-neutral elements.
- [ ] Account for every page or native block; missing or failed units must never be marked successful.
- [ ] Generate deterministic element and structural-chunk IDs from immutable revision, parse profile, and structural identity.
- [ ] Store raw parser output and rendered/page assets as immutable artifacts.
- [ ] Run parsers in isolation without ambient network access, provider credentials, or trust in embedded instructions.
- [ ] Add golden fixtures for English, Hindi, Hinglish, multi-column pages, tables, formulas, slides, malformed files, and unsupported blocks.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 5.3 — Confidence, OCR, and gated fallback

- [ ] Implement confidence capture per page and element.
- [ ] Use native extraction first and invoke OCR only for scanned or insufficient pages.
- [ ] Implement the documented OCR fallback adapter with English, Hindi, and Hinglish production fixtures.
- [ ] Keep handwriting visibly experimental and outside the blocking v1 corpus.
- [ ] Route low-confidence units to a deep-parser profile or promote with explicit warnings according to policy.
- [ ] Preserve original images and click-to-source regions for citation validation.
- [ ] Add timeout, decompression-bomb, malformed-file, oversized-image, prompt-injection, and parser-resource exhaustion tests.
- [ ] Measure character accuracy, structure, reading order, tables, formulas, and locators against EVAL-ING-004..011.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 5.4 — Shadow reprocessing, promotion, and projection events

- [ ] Implement immutable parse runs and parser-profile versions.
- [ ] Reprocessing must write a shadow run while the prior promoted run remains available.
- [ ] Validate completeness, provenance, deterministic identity, and policy gates before atomically moving the active parse pointer.
- [ ] Emit projection outbox events only after successful canonical promotion.
- [ ] Preserve historical parse runs, warnings, diagnostics, and active-version provenance.
- [ ] Implement safe retry, cancellation, dead-letter, and reprocess behavior without duplicate source revisions or elements.
- [ ] Add property tests for deterministic IDs and replay under crashes, duplicates, and out-of-order callbacks.
- [ ] Run the full EVAL-ING-001..012 ingestion gate suite and record corpus/profile hashes.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 5 exit gate

- [ ] Every accepted source retains its original, immutable revision metadata, normalized structure, provenance, and honest processing state.
- [ ] Same bytes plus parse profile produce identical revision, element, and chunk IDs in every rerun.
- [ ] No failed or omitted page is reported ready.
- [ ] Applicable English, Hindi, Hinglish, born-digital, scan, structure, reading-order, table, formula, locator, and retry thresholds in EVAL-ING-001..012 pass.
- [ ] Reprocessing cannot replace a valid active run until the shadow run passes promotion checks.
- [ ] Worker/process restart loses no accepted upload and creates no duplicate canonical records.
- [ ] Grok submits one consolidated Phase 5 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 5 ingestion and provenance audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 5 commit(s) and start of Phase 6.

# Phase 6 — Rich documents, canonical memory, conflicts, and proposed writes

Primary contracts: TRD-DOC-001..012, TRD-DATA-009..012, FSD-DOC-*, FSD-MEM-*, ADR-0008, ADR-0009.

## Micro-phase 6.1 — MemdotDocument v1 schema and backend model

- [ ] Implement the versioned MemdotDocument v1 JSON Schema exactly once in packages/contracts.
- [ ] Implement stable block IDs, document metadata, schema version, provenance, assets, citations, and supported rich node types.
- [ ] Preserve unknown or unsupported nodes losslessly as explicit placeholders rather than silently dropping them.
- [ ] Add deterministic canonical serialization and hash behavior.
- [ ] Add import/export adapters for Markdown and HTML as lossy views, not canonical state.
- [ ] Add sanitized rich-content validation for links, media, code, math, tables, SVG, and embedded metadata.
- [ ] Create exact round-trip and schema-migration fixtures, including unknown-node preservation.
- [ ] Run MemdotDocument v1 serialization, validation, migration-idempotency, and XSS corpus tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 6.2 — Immutable document revisions and conflict-safe saving

- [ ] Implement authored documents and immutable document revisions with current-revision pointers.
- [ ] Require every save to identify its base revision.
- [ ] Return 409 on stale-base save with safe current metadata and a block-diff token.
- [ ] Support explicit reload, copy-as-new, and reviewed merge paths; never use silent last-write-wins.
- [ ] Preserve revision history, author/agent attribution, citations, assets, and provenance.
- [ ] Ensure autosave retries are idempotent and cannot duplicate revisions.
- [ ] Add two-tab concurrency, split, merge, paste, duplicate-block, stale-base, retry, and historical-open tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 6.3 — Memory ontology, relations, and conflict sets

- [ ] Implement typed canonical memory records using the documented truth and provenance classes.
- [ ] Implement typed relations, source anchors, effective time, supersession, and unresolved/resolved conflict sets.
- [ ] Keep source assertions, user assertions, approved derived memory, external knowledge, conversation episodes, learner evidence, and system metadata distinguishable in storage and APIs.
- [ ] Ensure model confidence and retrieval rank cannot change a truth class.
- [ ] Keep pending, rejected, expired, deleted, and suppressed records outside ordinary retrieval.
- [ ] Implement revision history for approved memory and compensating records rather than destructive history edits.
- [ ] Add conflict coexistence, historical, source-superseded, deletion, and provenance tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 6.4 — Proposed writes and AI patch review

- [ ] Implement idempotent memory and document-patch proposal creation.
- [ ] Store proposer, model/client, target, immutable base revision, truth class, citations, duplicate/conflict status, and expiry policy.
- [ ] Implement first-party decisions: approve, edit and approve, reject, and delete pending.
- [ ] Make approval create a new canonical version in the same transaction as its outbox event.
- [ ] Make rejection change no canonical source, approved memory, document, or learner evidence.
- [ ] Mark base-drifted patches conflicted and require explicit rebase and review.
- [ ] Implement content-minimized audit history for proposal creation, inspection, decision, and resulting version.
- [ ] Test duplicate proposals, replayed decisions, stale patches, invalid citations, external-knowledge labels, and unauthorized approval.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 6 exit gate

- [ ] MemdotDocument v1 round-trips exactly and preserves unknown nodes.
- [ ] Document saves are immutable, idempotent, and conflict-safe with no silent overwrite.
- [ ] Truth, provenance, history, conflicts, and external-knowledge labels remain explicit.
- [ ] AI and external-agent writes remain pending until a first-party decision.
- [ ] Pending or rejected proposals never appear in normal retrieval or learning evidence.
- [ ] XSS, stale-base, concurrent-save, schema migration, proposal replay, and audit tests pass.
- [ ] Grok submits one consolidated Phase 6 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 6 document and memory-integrity audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 6 commit(s) and start of Phase 7.

# Phase 7 — Retrieval, Context Compiler, model routing, Tex, and OSS fallback

Primary contracts: TRD-RET-001..018, FSD-ASK-*, ADR-0003, ADR-0005, ADR-0006, EVAL-RET-001..007.

## Micro-phase 7.1 — Provider ports and local retrieval foundation

- [ ] Implement the MemoryProvider, embedding, reranking, and model-provider ports inside the domain boundary.
- [ ] Implement PostgreSQL exact retrieval using full-text search, trigram, identifiers, formulas, quoted phrases, dates, source/revision, and historical filters.
- [ ] Implement temporal and graph candidate lanes over canonical relations and curriculum/source anchors.
- [ ] Implement the local pgvector semantic projection and deterministic provider-to-canonical mapping.
- [ ] Store provider IDs only in derived projection tables and never expose them as public IDs or canonical foreign keys.
- [ ] Implement projection upsert, health, lag, tombstone, rebuild cursor, and idempotent replay.
- [ ] Add English, Hindi, Hinglish, code-mixed, Devanagari numeral, OCR-noise, formula, and code-identifier fixtures.
- [ ] Run exact, temporal, graph, local semantic, deletion, authorization, and projection-rebuild tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 7.2 — Query planner, fusion, reranking, and canonical post-filter

- [ ] Classify exact, semantic, graph, temporal, historical, conflict, course, source, and learning intent without widening caller authorization.
- [ ] Run eligible candidate lanes under bounded budgets and circuit breakers.
- [ ] Implement versioned weighted reciprocal-rank fusion with pinned exact hits.
- [ ] Apply bounded reranking without allowing the reranker to change eligibility, truth, version, or Private-Space policy.
- [ ] Rejoin every candidate to canonical PostgreSQL records under RLS.
- [ ] Reject unknown, deleted, retracted, stale-current, cross-account, Private-Space, unauthorized, and wrong-edition candidates after provider retrieval.
- [ ] Preserve an explicit historical or as-of query while default queries use current eligible evidence only.
- [ ] Add candidate-order shuffle, duplicate, distractor, provider-ID injection, stale projection, and permission-change tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 7.3 — Context Compiler, conflicts, citations, and receipts

- [ ] Implement scope resolution, retrieval routing, canonical hydration, structural expansion, conflict detection, deduplication, and budget packing.
- [ ] Preserve citation spans and immutable source/document revision locators.
- [ ] Generate absolute first-party user-openable URLs that reauthorize when opened.
- [ ] Produce immutable context receipts containing actor/purpose, scope, eligibility hash, routes, versions, included evidence, conflicts, omissions, budget decisions, provider state, and receipt ID.
- [ ] Exclude chain-of-thought, secrets, source instructions, and hidden policy text from receipts.
- [ ] Label unsupported or provider/model knowledge as External knowledge and never convert it into source truth.
- [ ] Implement source-first answer behavior, explicit abstention/clarification, and evidence-only response when generation is unavailable.
- [ ] Add prompt-injection, malicious-source, conflict, history, deletion, citation-open, budget, near-duplicate, and partial/degraded tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 7.4 — Model router, Tex adapter, fallback, and benchmarks

- [ ] Implement task-specific direct model adapters for embed, rerank, extract, summarize, answer, and grade.
- [ ] Enforce regional/provider policy, bounded stateless calls, disclosure, timeout, budget, disabled provider storage where supported, and no ambient credentials.
- [ ] Keep exact model versions as pinned deployment profiles selected through license and frozen-corpus gates.
- [ ] Implement the Tex adapter only through MemoryProvider; do not infer unavailable private Tex behavior.
- [ ] Make Tex optional and ensure outage opens the circuit to local exact, graph, temporal, pgvector, and local-rerank paths.
- [ ] Keep public IDs, authorization, revision selection, deletion, receipt format, and citations identical across Tex and fallback modes.
- [ ] Implement complete derived-index rebuild from PostgreSQL and object storage.
- [ ] Run lexical-only, dense-only, hybrid, hybrid-plus-reranker, Tex-primary, Tex-only diagnostic, Tex-down fallback, and Tex-rebuild benchmark modes.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 7 exit gate

- [ ] Overall retrieval meets EVAL-RET-001..007, including Recall@20 at least 0.90, nDCG@10 at least 0.80, exact Hit@5 at least 0.98, and zero stale-current evidence.
- [ ] Compiled context meets required evidence, precision, provenance, budget, duplicate, conflict, authorization, and citation gates.
- [ ] Generated-answer tests meet correctness, faithfulness, citation, unsupported-claim, locator, and abstention gates for the frozen profile.
- [ ] Tex-down fallback independently meets its exact, authorization, recall-retention, answer-delta, and citation requirements.
- [ ] Provider outage, timeout, 429/500, stale index, duplicate callback, and rebuild tests converge safely.
- [ ] MCP search latency is not yet the release gate, but Core search/context benchmarks identify whether TRD-OPS budgets remain achievable.
- [ ] Grok submits one consolidated Phase 7 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 7 retrieval, context, and provider audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 7 commit(s) and start of Phase 8.

# Phase 8 — Learning backend, Evidence Twin, assessment, and FSRS

Primary contracts: TRD-LRN-001..014, FSD-TST-*, FSD-REV-*, PRD-LEARN-001..007, ADR-0012, EVAL-LRN-001..008.

## Micro-phase 8.1 — Course, syllabus, concept, and prerequisite graph

- [ ] Implement Learning Spaces, courses, units, objectives, concepts, prerequisites, aliases, source coverage, and immutable source anchors.
- [ ] Distinguish suggested nodes and edges from confirmed curriculum truth.
- [ ] Prevent unconfirmed prerequisites from blocking progression.
- [ ] Enforce a cycle-free confirmed prerequisite graph.
- [ ] Preserve source revision and locator provenance for promoted graph records.
- [ ] Add versioned APIs for course setup, syllabus map, graph inspection, confirmation, correction, and source coverage.
- [ ] Update the TRD and generated OpenAPI if newly specified public Learning routes extend the founding route table.
- [ ] Run curriculum node, edge, anchor, cycle, suggestion, history, deletion, and authorization tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 8.2 — Versioned assessment and sealed grading

- [ ] Implement versioned MCQ, short-answer, and written explain/apply assessment items.
- [ ] Bind every item to immutable source, rubric, expected-answer, concept, and generation-profile versions.
- [ ] Keep answers and rubrics sealed before submission or explicit reveal.
- [ ] Capture response, response time, confidence before feedback, hints, reveal state, item/source versions, and client event ID.
- [ ] Implement deterministic grading for objective items and bounded model-assisted grading with confidence and provisional status for written items.
- [ ] Distinguish no hint, minor hint, substantive hint, revealed, skipped, post-feedback, ungradable, and retired-item outcomes.
- [ ] Add versioned APIs for test creation, session progression, submission, reveal, report-item, and results.
- [ ] Run sealed-answer, authorization, item-version, confidence-order, grading, hint, reveal, and retry tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 8.3 — Append-only learner events, Evidence Twin, and FSRS

- [ ] Implement append-only learner events with unique client event IDs and deterministic event ordering/replay.
- [ ] Implement eligibility policy so revealed, substantively hinted, post-feedback, low-confidence/ungradable, and otherwise ineligible events cannot raise demonstrated status.
- [ ] Separate exposure, practice, confidence, demonstrated recall, calibration, misconception, and source understanding.
- [ ] Implement Evidence Twin projections with complete event-to-state receipts.
- [ ] Implement item-level FSRS scheduling and explainable due reasons.
- [ ] Map Again, Hard, Good, and Easy according to the functional rules without treating self-confidence as truth.
- [ ] Make offline-submitted events provisional until idempotent server acknowledgement.
- [ ] Ensure conversations and externally recorded interactions cannot directly mutate learner evidence.
- [ ] Add projection rebuild, duplicate, out-of-order, correction, retirement, deletion, offline replay, and schedule-reason tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 8.4 — Learning evaluation and delayed-success instrumentation

- [ ] Implement the versioned learning benchmark graph, items, hidden splits, and event sequences.
- [ ] Measure curriculum node F1, edge precision/recall, source anchoring, cycles, deterministic replay, evidence eligibility, and sealed answers.
- [ ] Add property tests across hint/reveal/feedback/confidence/retirement/offline/deletion permutations.
- [ ] Add source-grounded delayed success measurement on novel eligible items.
- [ ] Keep engagement metrics separate from the north-star learning metric.
- [ ] Add content-free operational metrics for review scheduling and event-processing health.
- [ ] Run the complete EVAL-LRN-001..008 suite with fixture and algorithm hashes.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 8 exit gate

- [ ] Curriculum graph thresholds pass and confirmed prerequisites contain zero cycles.
- [ ] Every promoted learning node and relationship has source provenance.
- [ ] Sealed answers have zero pre-submission exposure.
- [ ] Event replay is exactly deterministic under duplicates and out-of-order delivery.
- [ ] No revealed, substantively hinted, post-feedback, ungradable, conversation-derived, or otherwise ineligible event raises demonstrated status.
- [ ] Evidence Twin and FSRS projections rebuild identically from append-only events.
- [ ] Source-grounded delayed success can be measured without using chat volume, time spent, streaks, or card counts as substitutes.
- [ ] Grok submits one consolidated Phase 8 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 8 learning-integrity audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 8 commit(s) and start of Phase 9.

# Phase 9 — MCP, OAuth, external AI, conversations, and capture

Primary contracts: TRD-MCP-001..012, TRD-API-001..005, FSD-INT-*, FSD-MEM-008..009, ADR-0007, ADR-0008.

## Micro-phase 9.1 — OAuth-protected MCP edge

- [ ] Implement Streamable HTTP MCP transport in apps/mcp as a thin Core client.
- [ ] Implement OAuth resource metadata, authorization challenge, PKCE S256, issuer, JWKS, audience, resource, expiry, scope, client identity, rotation, and revocation validation.
- [ ] Implement fixed scopes: memdot.memory.read, memdot.memory.propose, and memdot.interaction.record.
- [ ] Define memdot.memory.read as the whole eligible non-private account across current and future non-private Spaces, including relevant retained chats and completed attempts.
- [ ] Do not add v1 per-Space or per-data-class read selectors.
- [ ] Keep pending proposals, incomplete attempts, sealed answers, secrets, and Private Spaces excluded.
- [ ] Ensure the MCP edge cannot directly import database, Tex, object-store, or model adapters.
- [ ] Run wrong-issuer, wrong-audience, wrong-resource, expired, replayed, revoked, downgraded, missing-scope, and enumeration tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 9.2 — Compatible search and fetch tools

- [ ] Implement exact search({query}) input compatibility.
- [ ] Return result items with stable canonical ID, title, text/snippet, and absolute user-openable URL.
- [ ] Implement exact fetch({id}) input compatibility and reauthorize every fetch.
- [ ] Return immutable item, revision, citation, locator, truth/provenance, current/historical/conflict, and safe metadata required by the contract.
- [ ] Return identical machine data in structuredContent and JSON-serialized text content.
- [ ] Preserve search-to-fetch referential integrity and use no provider-internal identifiers.
- [ ] Return indistinguishable safe not-found behavior for unauthorized, Private-Space, and nonexistent items.
- [ ] Run JSON Schema, compatibility-shape, absolute-URL, reauthorization, pagination, deletion, history, conflict, and Private-Space tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 9.3 — Context, proposal, and interaction tools

- [ ] Implement prepare_context with explicit purpose, learning/general mode, hard budget, query, and allowed contract parameters.
- [ ] Return evidence, conflicts, omissions, degraded state, and immutable context receipt without hidden chain-of-thought.
- [ ] Implement propose_memory as an idempotent pending proposal only.
- [ ] Implement record_interaction as append-only explicit raw-turn capture with client, role, timestamp, receipt, target non-private Space, and declared completeness.
- [ ] Preserve single turn, partial thread, complete import, and unknown completeness states.
- [ ] State in tool descriptions and errors that MCP cannot passively inspect the host's complete conversation.
- [ ] Ensure record_interaction never commits source truth or changes learner evidence.
- [ ] Test duplicate calls, changed idempotency fingerprints, omitted surrounding turns, malicious content, Private-Space targets, stale receipt, and revoked grants.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 9.4 — Native and external conversation ledger

- [ ] Implement conversations, immutable turns, source client, capture method, completeness, receipt references, and retention state.
- [ ] Capture native Memdot chat turns automatically and mark them complete because Memdot owns both sides.
- [ ] Keep external capture best-effort and based only on explicit tool calls or imports.
- [ ] Implement paginated conversation and turn APIs with signed cursors.
- [ ] Implement user labels such as practice, confusion, insight, and candidate evidence without establishing demonstrated learning.
- [ ] Add durable conversation deletion initiation and immediate retrieval exclusion; complete purge behavior remains Phase 10.
- [ ] Add capture, pagination, replay, partial-thread, deletion-visibility, learning-firewall, and cross-account tests.
- [ ] Run the MCP/REST conformance harness and generated-client tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 9 exit gate

- [ ] All five MCP tools match their frozen names, schemas, annotations, side effects, and authorization.
- [ ] Search and fetch match the OpenAI-compatible company-knowledge shapes and use absolute reauthorized URLs.
- [ ] OAuth validation, private-space exclusion, error safety, revocation, and side-effect gates pass 100%.
- [ ] Whole-account consent includes relevant chats and completed attempts but cannot expose Private Spaces, pending proposals, incomplete attempts, or sealed answers.
- [ ] External capture never claims passive or universally complete host-chat access.
- [ ] Proposals remain pending and interaction capture leaves learner evidence unchanged.
- [ ] MCP search, fetch, context, write idempotency, deletion visibility, and compatibility harnesses pass.
- [ ] Grok submits one consolidated Phase 9 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 9 protocol, privacy, and capture audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 9 commit(s) and start of Phase 10.

# Phase 10 — Notion synchronization, export, deletion, and restore safety

Primary contracts: TRD-NOT-001..012, TRD-SEC-008..011, FSD-NOT-*, FSD-EXP-*, ADR-0014.

## Micro-phase 10.1 — Notion connection and selected-page inbound sync

- [ ] Implement the SourceConnector port and Notion adapter with encrypted OAuth tokens, least scopes, revocation, and recent-auth connection changes.
- [ ] Implement page discovery and explicit selected-page import into a destination Space.
- [ ] Fetch complete nested pagination, databases/pages as supported, comments only if in scope, and expiring assets into immutable object storage.
- [ ] Preserve unsupported blocks and lossy mappings as explicit warnings/placeholders.
- [ ] Store native page/block IDs only in connector mappings, never as public canonical IDs.
- [ ] Implement cursor persistence, polling/webhook reconciliation, missed-signal recovery, rate-limit Retry-After, and idempotent snapshot revisions.
- [ ] Keep selected sources outside the dedicated Memdot root inbound/read-only; never write to those remote pages.
- [ ] Run pagination, asset-expiry, unsupported-block, duplicate webhook, missed webhook, rate-limit, disconnect, permission-loss, and snapshot-idempotency tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 10.2 — Dedicated Memdot root two-way sync and conflicts

- [ ] Provision or select one dedicated Memdot root and show the exact write boundary.
- [ ] Allow write-back only for explicitly approved Memdot-authored documents mapped below that root.
- [ ] Store base Notion version, base Memdot revision, mapping, last successful sync, and transform profile.
- [ ] Implement idempotent one-sided propagation in either direction.
- [ ] Detect concurrent change from one base and pause only the affected item.
- [ ] Preserve base, Notion, and Memdot versions for Keep Notion, Keep Memdot, or reviewed merge.
- [ ] Never use silent last-write-wins or modify selected inbound pages outside the root.
- [ ] Run boundary, move/rename, concurrent-edit, delete, restore, retry, permission-change, and transformation-round-trip tests.
- [ ] Run the live authorized Notion test-workspace gate; if credentials are unavailable, report BLOCKED rather than simulating production success.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 10.3 — Portable export

- [ ] Implement durable item, conversation, Space, and complete-account export jobs requiring recent authentication.
- [ ] Export originals, immutable revisions, provenance, MemdotDocument JSON, best-effort Markdown/HTML, assets, approved memories, conversations/completeness, course graph, learner events, citations, and warnings.
- [ ] Add a machine-readable manifest with schema versions, hashes, counts, exclusions, and verification instructions.
- [ ] Exclude rebuildable provider embeddings and internal provider IDs.
- [ ] Use encrypted temporary export artifacts, expiring download URLs, access audit, retry, and purge.
- [ ] Test large exports, partial adapter loss, interrupted generation, retry, hash verification, authorization, expiry, and self-host portability.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 10.4 — Deletion orchestration and restore safety

- [ ] Implement source, conversation, Space, and account deletion workflows requiring scope confirmation and recent authentication.
- [ ] Immediately tombstone content and revoke affected sessions, grants, integrations, and keys before asynchronous purge.
- [ ] Make deletion win over ingestion, sync, projection, retry, callback, and restore.
- [ ] Purge live PostgreSQL content, immutable objects, exports, local indexes, Tex projections, caches, and connector mappings within the documented seven-day target.
- [ ] Retain only content-free irreversible deletion tombstones and purge checkpoints.
- [ ] Expire encrypted backups within 35 days and replay tombstones before any restored data can be served or reprojected.
- [ ] Expose durable deletion stages, failures, retry/operator escalation, and irreversibility without provider-internal leakage.
- [ ] Run deletion-during-job, provider-timeout, partial purge, duplicate purge, restore, reimport, reprojection, backup, and account-revocation tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 10 exit gate

- [ ] Notion selected-page inbound sync, dedicated-root write boundary, assets, pagination, idempotency, and explicit three-way conflict behavior pass.
- [ ] The live authorized Notion workspace gate passes before two-way sync is called complete.
- [ ] Portable exports are complete, hashed, versioned, and usable without Tex.
- [ ] Deletion becomes externally invisible immediately and completes across canonical, object, connector, Tex, local projection, cache, export, and backup paths.
- [ ] Restore drills prove deleted data cannot become current, searchable, fetchable, syncable, or reprojected.
- [ ] Revocation and deletion errors reveal no Private-Space or provider-internal information.
- [ ] Grok submits one consolidated Phase 10 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 10 integration and lifecycle audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 10 commit(s) and start of Phase 11.

# Phase 11 — Security hardening, observability, deployment, and evaluation platform

Primary contracts: TRD-SEC-001..014, TRD-DEP-001..008, TRD-OPS-001..013, Security and Privacy Threat Model, Evaluation and Release Gates.

## Micro-phase 11.1 — Security controls and content-safe observability

- [ ] Implement a strict telemetry allowlist for content-free request, workflow, provider, receipt, queue, deletion, and SLO metadata.
- [ ] Prohibit prompts, responses, queries, titles, filenames, source text, answers, cookies, authorization headers, and credentials from logs, traces, metrics, analytics, and crash reports.
- [ ] Add automated log-sink tests that exercise sensitive fixtures and fail on forbidden content.
- [ ] Implement product analytics as a separate opt-in that is off by default; keep session replay and research-content donation outside v1 defaults.
- [ ] Implement administrative MFA, just-in-time authorization, reason capture, recent authentication, and content-free audit boundaries.
- [ ] Add parser/model isolation, SSRF, prompt-injection, XSS, malicious archive, secret-redaction, dependency, and container-hardening tests.
- [ ] Implement incident-severity, containment, key/token revocation, provider-disable, deletion protection, and user-notification runbooks.
- [ ] Run threat-model launch gates and record unresolved legal or operational decisions as blockers.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 11.2 — Resilience, backpressure, SLOs, and failure injection

- [ ] Implement circuit breakers and bulkheads for Tex, model providers, Notion, OCR, object storage, and optional reranking.
- [ ] Implement file-size, request-rate, concurrency, queue-depth, provider-budget, abuse, and system-safety controls without monthly product quotas.
- [ ] Preserve accepted work durably and reject only before acceptance with actionable 429, Retry-After, queued, partial, or degraded states.
- [ ] Add content-free metrics and alerts for latency, errors, queue age/depth, projection lag, rejection reasons, context degradation, citation validity, circuit state, deletion checkpoints, token/cost, and SLO burn.
- [ ] Page immediately on cross-account/private candidate detection, deletion resurrection, canonical-store outage, authentication bypass indicators, and learner-state corruption.
- [ ] Run failure injection across process crash, dependency outage, timeout, 429/500, overload, poison job, stale projection, and partial deletion.
- [ ] Measure TRD-OPS-001..008 budgets and document every miss without weakening targets.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 11.3 — Hosted India-first GCP infrastructure

- [ ] Implement version-controlled hosted infrastructure for Mumbai asia-south1 stateless web, Core, MCP, workers, and model-router workloads.
- [ ] Implement regional GKE, Cloud SQL PostgreSQL HA, private GCS, regional Artifact Registry and log buckets, Cloud KMS, and Secret Manager boundaries.
- [ ] Implement Delhi asia-south2 encrypted disaster-recovery backup configuration only.
- [ ] Apply organization policy restricting content-bearing resources to approved India locations.
- [ ] Keep DNS, certificate, and content-free edge metadata explicitly separated from content-bearing resources.
- [ ] Configure workload identity, private networking, least-privilege service accounts, egress controls, and regional model endpoints.
- [ ] Implement separate bounded migration jobs and expand, migrate, contract deployment sequencing.
- [ ] Validate infrastructure formatting, policy, security scanning, plan output, region assertions, and destructive-change detection without deploying until Tauqueer authorizes it.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 11.4 — Supply chain, self-host parity, and benchmark platform

- [ ] Pin images and dependencies by version or digest and generate reproducible build metadata.
- [ ] Generate SBOMs, vulnerability reports, provenance, signatures, and license records for application images and approved model weights.
- [ ] Implement the versioned Memdot Memory Benchmark layout: corpus, elements, tasks, qrels, graph gold, and security vectors.
- [ ] Build deterministic runners for parser, retrieval, context, answer, learner, MCP, REST, Notion, PWA, security, performance, fallback, restore, and deletion gates.
- [ ] Store corpus, configuration, source, parser/index/model, output, judge, and result hashes.
- [ ] Create per-PR smoke, nightly full benchmark, release-candidate, and weekly-beta review jobs without using user content.
- [ ] Run the full self-host acceptance path with Tex disabled, telemetry export off, local retrieval, and a supported local or explicitly configured model endpoint.
- [ ] Prove hosted and self-host modes use identical migrations, exports, events, domain rules, and public contracts.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 11 exit gate

- [ ] Threat-model controls, telemetry denylist, administrative controls, and incident runbooks pass security review.
- [ ] Backpressure and dependency failure degrade or queue work without loss, unbounded spend, or widened authorization.
- [ ] Search, fetch, context, accepted-write, availability, ingestion, projection, revoke, RPO, and RTO measurements are captured against TRD targets.
- [ ] Hosted infrastructure plans keep canonical content and managed inference in Mumbai with Delhi limited to encrypted disaster-recovery backups.
- [ ] Images and dependencies are pinned, scanned, SBOM-generated, provenance-recorded, and reproducible.
- [ ] Tex-disabled self-host acceptance passes with telemetry export off.
- [ ] The versioned evaluation platform produces reproducible result artifacts and hashes.
- [ ] Grok submits one consolidated Phase 11 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 11 security, operations, deployment, and evaluation audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 11 commit(s) and start of Phase 12.

# Phase 12 — Frontend foundation, authentication, responsive shell, and PWA base

Frontend implementation begins here. No prior phase may hide unfinished backend behavior behind UI mocks.

Primary contracts: TRD-SYS-001, FSD-NAV-*, FSD-AUTH-*, FSD-ONB-*, FSD-ERR-*, FSD-A11Y-*, ADR-0013.

## Micro-phase 12.1 — Next.js application architecture and generated API client

- [ ] Configure the production Next.js application to consume only generated public contracts and first-party Core APIs.
- [ ] Establish server/client boundaries so authenticated memory is not leaked into static output, shared caches, logs, or third-party telemetry.
- [ ] Implement session bootstrap, CSRF handling, safe request wrappers, signed-cursor handling, problem+json mapping, retry policy, and correlation-ID display.
- [ ] Add frontend feature boundaries for Today, Library, Spaces, Ask, Test, Review, Memory, Integrations, and Settings without implementing complete screens.
- [ ] Add shared state primitives for loading, empty, partial, degraded, unauthorized, stale, offline, queued, rate-safe, and failure states.
- [ ] Add frontend dependency-boundary checks preventing direct datastore, provider, or model-vendor access.
- [ ] Run build, lint, type-check, generated-client freshness, request-wrapper, cache-safety, and route-smoke tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 12.2 — Authentication, adult confirmation, and onboarding

- [ ] Implement Google-only hosted sign-in presentation and self-host OIDC/operator presentation.
- [ ] Implement explicit 18+ confirmation before hosted account activation.
- [ ] Show a clear adults-only rejection path without collecting date of birth or identity documents.
- [ ] Implement first setup for display name, timezone, English UI, English/Hindi/Hinglish content preferences, first Space, and optional Learning Space.
- [ ] Implement session expiry, logout, account switch, recent-auth prompts, CSRF failure, provider failure, and retry states.
- [ ] Ensure no authenticated content is cached before account activation.
- [ ] Run keyboard, screen-reader, mobile, session, CSRF, activation, rejection, refresh, and logout tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 12.3 — Accessible design system, shell, and navigation

- [ ] Implement accessible shared primitives for inputs, dialogs, sheets, menus, tables, trees, tabs, toasts, progress, citations, conflict labels, status badges, and destructive confirmations.
- [ ] Implement responsive desktop sidebar, mobile navigation, command/search entry, global job status, and account menu.
- [ ] Implement route shells for every v1 surface with correct authorization and empty/loading/error states.
- [ ] Preserve visible focus, logical tab order, focus trap/restore, reduced motion, zoom/reflow, touch targets, and non-color state cues.
- [ ] Support Unicode-safe Hindi, Devanagari, and Hinglish content while UI chrome remains English.
- [ ] Add Storybook or equivalent isolated component verification only if it does not become a parallel product UI.
- [ ] Run automated accessibility, keyboard, screen-reader smoke, responsive viewport, high zoom, reduced-motion, and component-state tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 12.4 — PWA installation and offline security foundation

- [ ] Implement installable manifest, icons, service worker, update lifecycle, and explicit online/offline state.
- [ ] Cache only the public shell by default; authenticated content requires explicit pin or review-pack download.
- [ ] Implement account-partitioned encrypted IndexedDB with a non-extractable per-device key.
- [ ] Clear the account namespace and key on logout or account switch.
- [ ] Implement stale revision labels, storage/quota status, eviction handling, per-device removal, and clear-all.
- [ ] Prevent service-worker activation from replacing an active test or dirty editor.
- [ ] Keep Ask, global search, imports, sync, MCP, settings/security changes, new test generation, and document editing disabled offline.
- [ ] Run cold launch, install, update, account isolation, logout purge, eviction, stale badge, unsupported browser, and offline-action denial tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 12 exit gate

- [ ] The frontend uses generated contracts and contains no domain authorization or provider shortcuts.
- [ ] Hosted Google sign-in, 18+ confirmation, onboarding, session failure, recent authentication, and logout flows pass.
- [ ] Every v1 route has an accessible responsive shell and explicit global states.
- [ ] WCAG-oriented component, keyboard, focus, screen-reader smoke, touch, zoom, and responsive tests pass.
- [ ] PWA installation, safe update, explicit pinning, encrypted account partitioning, logout purge, and offline-denial rules pass.
- [ ] No product surface falsely claims unavailable backend capability.
- [ ] Grok submits one consolidated Phase 12 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 12 frontend-foundation and offline-security audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 12 commit(s) and start of Phase 13.

# Phase 13 — Frontend General Memory, editor, ingestion, Ask, and Memory

Primary contracts: FSD-TOD-*, FSD-LIB-*, FSD-SRC-*, FSD-SPC-*, FSD-DOC-*, FSD-ING-*, FSD-ASK-*, FSD-MEM-*.

## Micro-phase 13.1 — Today, Library, Spaces, and source detail

- [ ] Implement Today with due review, active jobs, recent Spaces/sources, proposals, conflicts, and trustworthy degraded-state summaries.
- [ ] Implement Library search, filters, sort, current/history state, source type, processing state, and destination Space.
- [ ] Implement General, Learning, and Private Space creation, rename, archive, restore, delete, and privacy explanation.
- [ ] Warn that changing a Space from Private to non-private makes it eligible for existing whole-account external-AI grants.
- [ ] Implement source detail with original/current revision, version history, processing stages, warnings, provenance, citations, reprocess, and deletion.
- [ ] Support historical version inspection and explicit source conflicts.
- [ ] Run route, authorization, empty, partial, degraded, history, conflict, Private-Space, responsive, keyboard, and screen-reader tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 13.2 — Upload, processing, failure, and reprocessing UI

- [ ] Implement upload and paste with destination Space, detected type, size/page safeguards, checksum progress, and durable acceptance.
- [ ] Implement queued, processing stage, partial, low-confidence, ready-with-warnings, ready, failed, retryable, refused-before-acceptance, and overload states.
- [ ] Show page/element warnings and experimental handwriting labeling without implying full completeness.
- [ ] Preserve job status across refresh, reconnect, route change, and worker retry.
- [ ] Implement safe reprocess and parser-profile comparison without replacing active results prematurely.
- [ ] Implement global job-status integration and user-safe correlation IDs.
- [ ] Run upload interruption, duplicate completion, reconnect, queue overload, parser crash, low-confidence, reprocess, accessibility, and mobile tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 13.3 — Rich editor, revision history, AI patch review, and conflicts

- [ ] Implement the Tiptap editor as a MemdotDocument v1 adapter rather than canonical HTML.
- [ ] Implement headings, lists, tables, code, math, media, citations, backlinks, and supported rich blocks with stable block IDs.
- [ ] Implement save state, revision history, historical open, source citations, and content-safe rendering.
- [ ] Implement stale-base conflict flows for reload, copy-as-new, and explicit reviewed merge.
- [ ] Implement AI patch proposal preview with additions, removals, citations, truth labels, target base, duplicate/conflict state, approve, edit and approve, and reject.
- [ ] Keep general offline editing disabled; use only an encrypted dirty buffer for connection-drop recovery and submit under normal revision checks after reconnect.
- [ ] Run exact document round-trip, block-ID, two-tab, patch base-drift, XSS, dirty-buffer, keyboard, screen-reader, touch, and responsive tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 13.4 — Ask, global search, receipts, Memory, and activity

- [ ] Implement source-first Ask with account, Space, course, source, concept, current, and historical scopes supported by the backend.
- [ ] Show citations, immutable versions, conflicts, unsupported claims, External knowledge labels, omissions, and degraded state.
- [ ] Implement context-receipt inspection without revealing chain-of-thought.
- [ ] Implement global search with result type, Space, source/version, snippet, stable URL, history, and conflict state.
- [ ] Implement Memory Proposed, Stored, and Activity surfaces.
- [ ] Implement proposal approve, edit and approve, reject, duplicate/conflict review, stored-item history, provenance, citations, relations, projection health, suppress, delete, and reindex where allowed.
- [ ] Show native/external conversation source and completeness accurately.
- [ ] Run search/fetch referential, citation-open, history, conflict, External knowledge, proposal, activity, deletion, degraded, accessibility, and responsive tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 13 exit gate

- [ ] Today, Library, Spaces, Private Spaces, source detail, ingestion, editor, Ask, search, receipts, Memory, and activity satisfy their FSD requirements.
- [ ] Every user-visible state has a matching technical recovery path.
- [ ] Historical versions and unresolved conflicts remain visible and cannot be silently collapsed.
- [ ] AI edits and memories remain reviewable proposals until approval.
- [ ] Source-first answers cite immutable revisions and clearly label External knowledge.
- [ ] Editor round-trip, XSS, concurrent-save, ingestion-recovery, citation, receipt, proposal, accessibility, and responsive suites pass.
- [ ] Grok submits one consolidated Phase 13 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 13 General Memory UX and contract audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 13 commit(s) and start of Phase 14.

# Phase 14 — Frontend Learning, integrations, settings, offline, and accessibility

Primary contracts: FSD-SPC-*, FSD-ASK-*, FSD-TST-*, FSD-REV-*, FSD-INT-*, FSD-SET-*, FSD-EXP-*, FSD-OFF-*, FSD-A11Y-*.

## Micro-phase 14.1 — Learning setup, course map, and coverage

- [ ] Implement Learning Space and course setup from syllabus, source selection, manual structure, and suggestions.
- [ ] Implement the syllabus-tree-first course map with units, objectives, concepts, prerequisites, source coverage, confirmation, correction, and conflict indicators.
- [ ] Distinguish suggested and confirmed nodes/edges visually and semantically.
- [ ] Ensure unconfirmed prerequisites never block progression.
- [ ] Implement concept/source detail and navigation into Ask, Test, and Review.
- [ ] Add keyboard tree navigation, screen-reader structure, touch behavior, responsive alternative, and non-color state cues.
- [ ] Run setup, graph, confirmation, cycle-error, coverage, source-anchor, authorization, accessibility, and responsive tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 14.2 — Test, results, Review, and Evidence Twin UI

- [ ] Implement Test setup by course/concept/source, item types, difficulty, count, and supported goals.
- [ ] Implement one-item-at-a-time MCQ, short-answer, and written response flows with confidence captured before feedback.
- [ ] Keep answers and rubrics sealed until submission or explicit reveal.
- [ ] Implement hints, reveal, skip, provisional grading, report item, source/rubric versions, and clear practice-only reasons.
- [ ] Implement results with corrections, citations, confidence calibration, event receipts, Evidence Twin changes, and scheduled reviews.
- [ ] Implement Review due counts, filters, due reasons, item flow, Again/Hard/Good/Easy explanation, summary, and next-due state.
- [ ] Make source-grounded delayed success visible separately from engagement metrics.
- [ ] Run answer-sealing, hint/reveal eligibility, confidence order, provisional grading, event receipt, FSRS explanation, keyboard, screen-reader, touch, and responsive tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 14.3 — MCP, Notion, provider, and privacy settings UI

- [ ] Implement integration cards for Notion, external AI/MCP clients, managed model, and optional BYOK adapters.
- [ ] Implement whole-account external-AI consent that names all current/future non-private Spaces, relevant retained chats, completed attempts, fixed private exclusion, downstream-provider risk, and inability to claw back returned data.
- [ ] Display read, propose-memory, and record-interaction grants separately and allow read-only connection.
- [ ] Implement connection activity, last access/sync, capture completeness, failures, reconnect, immediate revoke, and prior-disclosure explanation.
- [ ] Implement Notion selected-page import, dedicated Memdot root, sync status, warnings, permission loss, disconnect, and three-way conflict review.
- [ ] Implement provider/BYOK disclosure for region, retention/training controls, credential owner, cost, test, save, revoke, and delete.
- [ ] Implement Profile, AI, Privacy, Offline, data controls, analytics opt-in off, research donation off, and no v1 billing/quota meter.
- [ ] Run consent comprehension, Private-Space, scope, revoke, Notion boundary/conflict, BYOK secret, provider-outage, accessibility, and responsive tests.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 14.4 — Export, deletion, operational status, and offline review

- [ ] Implement item, conversation, Space, and account export with recent-auth, durable status, manifest summary, expiring download, and failure recovery.
- [ ] Implement scoped deletion confirmations, immediate invisibility/revocation, durable purge stages, backup expiry explanation, failure escalation, and irreversible boundary.
- [ ] Implement offline pinned reading with revision time, stale state, locally available citations, assets, storage, unpin, and eviction recovery.
- [ ] Implement downloadable seven-day review packs with creation/expiry, course/item summary, sealed answer protection, provisional response state, idempotent replay, and reconciliation.
- [ ] Implement global status for ingestion, sync, export, deletion, projection rebuild, provider outage, queue protection, and offline replay.
- [ ] Complete manual WCAG 2.2 AA-oriented review for authentication, ingestion, editor, Ask, Test, Review, proposals, consent, export, deletion, and offline flows.
- [ ] Run Chromium, WebKit, Firefox, installed iOS/Android PWA smoke, keyboard-only, screen-reader, touch, zoom/reflow, reduced-motion, Unicode, offline, and responsive test matrices.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 14 exit gate

- [ ] Learning map, Test, Review, Evidence Twin, confidence, citations, and due-reason experiences satisfy all linked FSD requirements.
- [ ] No sealed answer leaks and no ineligible attempt is presented as demonstrated learning.
- [ ] Whole-account consent, Private-Space exclusion, capture completeness, revocation, Notion boundary, and provider disclosure are explicit.
- [ ] Offline behavior is limited to pinned reading and seven-day review packs; replay remains provisional until acknowledged.
- [ ] Export, deletion, job status, degraded operation, and failure recovery are visible and honest.
- [ ] Required browser, installed-PWA, keyboard, screen-reader, touch, responsive, and WCAG-oriented gates pass.
- [ ] Grok submits one consolidated Phase 14 report using docs/execution/PHASE_REPORT_TEMPLATE.md.
- [ ] Codex performs a complete Phase 14 Learning, integration, privacy, offline, and accessibility audit and returns PASS.
- [ ] Tauqueer explicitly authorizes the Phase 14 commit(s) and start of Phase 15.

# Phase 15 — Release candidate, full-system acceptance, and beta launch readiness

Primary contracts: PRD section 14, FSD-AC-001..024, TRD section 14, System Architecture section 19, all Security and Evaluation release gates.

## Micro-phase 15.1 — Cross-document end-to-end acceptance

- [ ] Run FSD-AC-001..024 as automated end-to-end tests where feasible and documented manual tests where human judgment is required.
- [ ] Verify Google signup and 18+ activation.
- [ ] Verify public free enrollment with safety limits but no advertised monthly quota.
- [ ] Verify file and Notion ingestion with deterministic revisions and citations.
- [ ] Verify rich-document authoring, revision conflicts, and proposed AI edits.
- [ ] Verify source-first Ask with labeled External knowledge, conflicts, history, and receipts.
- [ ] Verify whole-account external-AI retrieval excluding Private Spaces.
- [ ] Verify best-effort external capture and memory-proposal approval.
- [ ] Verify course mapping, Test, eligible evidence, Evidence Twin, and Review scheduling.
- [ ] Verify Tex outage with OSS fallback and fully functional Tex-disabled self-host deployment.
- [ ] Verify offline pinned reading and provisional review replay.
- [ ] Verify complete export and deletion without resurrection.
- [ ] Publish an acceptance matrix linking every scenario to test artifact, commit, environment, and result.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 15.2 — Frozen benchmark, performance, and adversarial security

- [ ] Freeze the beta benchmark corpus, labels, split, configurations, and hashes.
- [ ] Run the full parser, retrieval, context, answer, conflict/history, learner, Tex/fallback, MCP/REST, editor, Notion, PWA, resilience, and safety suites.
- [ ] Run three generative evaluations and publish variance plus the stratified human citation audit.
- [ ] Run at least 10,000 adversarial cross-account and Private-Space calls with zero leakage.
- [ ] Run prompt-injection, OAuth, enumeration, sealed-answer, deleted-data, telemetry-content, secret, and provider-egress attacks.
- [ ] Run load and soak tests for search, fetch, context, accepted writes, ingestion queues, projection lag, revocation, and provider budgets.
- [ ] Verify MCP search p95 at most 1.5 seconds, fetch p95 at most 500 ms, context p95 at most 3 seconds excluding generation, and successful tool calls at least 99.5% excluding valid client errors.
- [ ] Treat any cross-account leak, Private-Space leak, invalid-current citation, sealed-answer leak, deleted-data resurrection, or learner-state corruption as an automatic FAIL.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 15.3 — Live integration, restore, deployment, and incident rehearsal

- [ ] Run live compatibility tests against ChatGPT, Claude remote MCP, and Gemini CLI; do not claim untested consumer-Gemini compatibility.
- [ ] Run the live authorized Notion workspace suite for pagination, assets, missed webhooks, rate limits, write boundary, conflicts, deletion, and disconnect.
- [ ] Run managed-model and approved BYOK region/retention disclosure tests using release-pinned configurations.
- [ ] Run a clean Tex-disabled self-host installation from published artifacts.
- [ ] Run hosted infrastructure plan review and, only after Tauqueer authorizes deployment, a Mumbai staging deployment with Delhi backup policy.
- [ ] Run database/object restore, deletion-tombstone replay, RPO at most 15 minutes, and RTO at most 4 hours drills.
- [ ] Rehearse Tex outage, model outage, Notion outage, object/database outage, overload, credential compromise, and suspected privacy incident.
- [ ] Verify rollback, provider disable, revocation, status communication, evidence preservation, and post-incident audit procedures.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Micro-phase 15.4 — Documentation, legal, manual QA, and release decision

- [ ] Update all implementation-status documentation, verified commands, paths, ownership, diagrams, APIs, migrations, events, deployment instructions, operations runbooks, and traceability.
- [ ] Verify Apache 2.0 notices, third-party licenses, model licenses, SBOMs, image signatures, provenance, and vulnerability disposition.
- [ ] Complete the prelaunch Indian legal review for adult-only enrollment, consent notices, processor disclosures, retention, export, deletion, security audits, and DPDP interactions.
- [ ] Complete founder manual QA on desktop and mobile for every named route and critical degraded/failure state.
- [ ] Resolve or explicitly owner-defer every release blocker; no critical security, privacy, data-integrity, citation, learning-integrity, deletion, or accessibility blocker may be deferred.
- [ ] Freeze release versions for application images, schemas, migrations, benchmark, models, provider profiles, runbooks, and public documentation.
- [ ] Record the micro-phase self-check in working notes and continue only if it passes.
- [ ] Grok self-check: PENDING.

## Phase 15 exit gate

- [ ] Every FSD-AC scenario and System Architecture validation-matrix row has passing evidence.
- [ ] Every hard Evaluation and Release Gate meets its absolute threshold.
- [ ] Every PRD requirement maps to implemented behavior, technical ownership, tests, and current documentation.
- [ ] Every public interface has validated authorization, schema, error, idempotency, pagination, retry, revocation, and deletion behavior.
- [ ] Every documented failure has a visible user state, technical recovery, and tested operational runbook.
- [ ] Hosted and self-hosted releases preserve the same domain contracts and feature workflows.
- [ ] Zero known cross-account leakage, Private-Space leakage, invalid-current citation, sealed-answer leakage, deleted-data resurrection, or learner-state corruption remains.
- [ ] Grok supplies the consolidated final release evidence bundle using docs/execution/PHASE_REPORT_TEMPLATE.md without committing, merging, or deploying beyond prior explicit authorization.
- [ ] Codex performs the final architecture, code, security, test, documentation, and release-evidence audit.
- [ ] Final Codex verdict is PASS.
- [ ] Tauqueer makes the explicit go, no-go, commit, tag, merge, deploy, and public-beta decision.

# 4. Recurring review checklists

## 4.1 Database or migration change

- [ ] Ownership and account/Space keys are explicit.
- [ ] FORCE RLS and adversarial policies exist before use.
- [ ] Foreign keys cannot attach across accounts.
- [ ] Immutable or append-only rules are enforced in the database where feasible.
- [ ] Migration follows expand, migrate, contract compatibility.
- [ ] Clean install and upgrade paths pass.
- [ ] Backup/restore and deletion-tombstone effects are considered.
- [ ] Generated schema and documentation are updated.

## 4.2 Public API, MCP, event, or schema change

- [ ] Canonical owner is identified.
- [ ] Requirement and version impact are documented.
- [ ] Generated consumers are refreshed.
- [ ] Backward compatibility is tested.
- [ ] Authorization, Private-Space, recent-auth, and scope behavior are tested.
- [ ] Idempotency, pagination, errors, retry, revoke, and deletion are tested.
- [ ] Safe content-free logs and errors are verified.
- [ ] Examples contain no secrets or personal data.

## 4.3 Provider or model change

- [ ] Provider implements a stable inward-facing port.
- [ ] Provider IDs remain derived and private.
- [ ] Canonical post-filter and RLS rejoin remain mandatory.
- [ ] Region, retention, training, storage, credential, cost, license, and disclosure behavior are recorded.
- [ ] Timeouts, retries, circuit breaker, budget, and degraded path are tested.
- [ ] Tex-disabled or provider-disabled workflow remains functional.
- [ ] Frozen benchmarks pass without hidden critical-slice regression.

## 4.4 User-facing change

- [ ] FSD route, states, and Given/When/Then acceptance are linked.
- [ ] Loading, empty, partial, degraded, unauthorized, stale, offline, rate-safe, and failure behavior are implemented where relevant.
- [ ] Keyboard, screen reader, focus, touch, zoom/reflow, reduced motion, responsive, and non-color cues are tested.
- [ ] English UI and English/Hindi/Hinglish content behavior are preserved.
- [ ] Telemetry and caches contain no prohibited content.
- [ ] Documentation and screenshots reflect actual behavior.

## 4.5 Security, privacy, export, or deletion change

- [ ] Threat boundary and abuse cases are named.
- [ ] Cross-account and Private-Space adversarial tests pass.
- [ ] Secrets and source content are absent from logs and errors.
- [ ] Recent authentication and revocation behavior are correct.
- [ ] Export contains required portable canonical data and hashes.
- [ ] Deletion becomes immediately invisible and wins over every in-flight job.
- [ ] Provider purge and restore tombstone replay are verified.
- [ ] Incident and operator recovery behavior is documented.

# 5. Progress and decision log

- [x] Current active macro-phase: Phase 3 — owner-authorized; implementation not started.
- [ ] Current internal micro-phase: Phase 3.1 not started.
- [ ] Current Grok phase report: NONE for Phase 3.
- [x] Current Codex verdict: PASS for Phases 1 and 2.
- [x] Current owner decision: Phase 2 commit and Phase 3 start authorized.
- [ ] Current blocker: NONE.
- [x] Last accepted implementation: Phase 2 self-host platform in the commit recording this transition.
- [x] Last verified environment: Node 22 (`.nvmrc` / CI / containers); Python 3.12 (`.python-version` / CI / containers); pnpm 11.5.2; uv with `uv.lock`; Docker Compose v5.3.0.
- [x] Last documentation synchronization: 2026-07-16 Phase 2 accepted and Phase 3 started by owner decision.

## Accepted macro-phase record template

- [ ] Macro-phase:
- [ ] Completed micro-phase self-checks:
- [ ] Grok phase-report date:
- [ ] Codex verdict:
- [ ] Correction rounds:
- [ ] Owner-authorized commit:
- [ ] Commit hash:
- [ ] Test artifact:
- [ ] Benchmark/profile hash:
- [ ] Documentation updated:
- [ ] Remaining non-blocking follow-up:

# 6. Definition of complete

- [ ] Code exists in the documented ownership boundary.
- [ ] Behavior satisfies the linked PRD, FSD, TRD, ADR, security, and evaluation requirements.
- [ ] Database, contract, provider, UI, and deployment changes are versioned and documented.
- [ ] Required unit, property, contract, integration, end-to-end, security, accessibility, benchmark, performance, failure-injection, and restore tests pass.
- [ ] No unexplained skips, warnings, flaky reruns, hidden fixtures, or manual-only substitutions remain.
- [ ] Current paths and commands are reflected in AGENTS.md and Codebase Context Map.
- [ ] Grok has provided one complete phase-level evidence handoff.
- [ ] Codex has returned PASS.
- [ ] Tauqueer has explicitly authorized the commit and next step.
