# Memdot Execution Context

Version: 1.0
Baseline date: 2026-07-15
Purpose: Durable starting context for Grok, Codex, and future implementation sessions

## 1. Current verified repository state

- The workspace contains the founding product, functional, technical,
  architecture, ADR, security, evaluation, AI-context, implementation-plan, and
  implementation-tracker documents.
- Phase 1 monorepo scaffold is accepted at
  `4138239ea31eff267af3e9a9d9984ca51a763991`.
- Phase 2 self-host infrastructure is **accepted after Codex PASS and owner
  commit authorization**. Live
  `make selfhost-smoke` passed on system `dockerd` (`unix:///var/run/docker.sock`)
  as project `memdot-smoke-20260716024239-1851798` (Tex off, telemetry off;
  durable canary effect count 1; accepted-work Hatchet restart; truthful
  readiness degradation/recovery). Phase 3 is owner-authorized and active; its
  implementation has not started.
- No product domain schema, application authz, ingestion, retrieval, Learning,
  MCP tools, Notion, or Tex provider wiring is claimed complete.
- Verified scaffold paths exist for apps/web, apps/mcp, services/core,
  services/workers, services/model-router, packages/contracts,
  packages/domain-python, packages/provider-adapters, packages/ui,
  infra/compose, infra/hosted, tests/benchmark, and tests/security.
- Git branch `main` contains the accepted Phase 1 base and Phase 2 handoff; this
  transition commit records the accepted self-host platform and Phase 3 start.
- Verified commands are recorded in AGENTS.md and
  docs/ai/CODEBASE_CONTEXT_MAP.md.
- This file must be updated whenever a phase changes verified repository state.

## 2. Roles and decision flow

- Tauqueer is the product owner and final decision maker.
- Grok is the implementation builder inside Cursor.
- Codex is the senior technical architect and phase-level code reviewer.
- Tauqueer starts a macro-phase.
- Grok completes every micro-phase in order, self-checking and fixing its logic
  between micro-phases.
- Grok sends one consolidated report only at the macro-phase boundary.
- Codex audits the complete diff and evidence against the documentation map.
- A Codex PASS makes the phase eligible for an owner-authorized commit.
- FAIL keeps the same phase open for corrections.
- Commit, push, merge, deploy, credentials, paid resources, production data, and
  phase transitions remain owner-controlled.

## 3. Required reading order

1. [AGENTS.md](AGENTS.md)
2. This context file.
3. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
4. The active phase in [IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md)
5. [Documentation index](docs/README.md)
6. The active phase's mapped PRD, FSD, TRD, ADR, architecture, threat, and
   evaluation sections.
7. [Codebase Context Map](docs/ai/CODEBASE_CONTEXT_MAP.md)
8. The actual repository files, manifests, migrations, tests, and CI.

Target documents never prove implementation state. Inspect the code and raw test
results.

## 4. Locked product contract

- Memdot is a general memory platform with Learning as its first flagship mode.
- Hosted beta is public, free, Google-auth-only, and restricted to users
  confirming they are 18+.
- UI launches in English.
- Ingestion, OCR, memory, exact/semantic retrieval, and citations support
  English, Hindi, and Hinglish against the production corpus.
- Connected external AI clients can retrieve the complete eligible non-private
  account, including relevant retained chats and completed attempts.
- Private Spaces are categorically excluded from external AI.
- Native chats are captured automatically.
- External chat capture is best-effort through explicit MCP calls or imports;
  MCP cannot passively observe a host's complete conversation.
- User content remains until the user explicitly deletes it.
- External knowledge is labelled and never silently converted into source truth.
- AI-created memories, relationships, facts, and document edits are proposals
  requiring first-party review.
- The beta advertises no monthly user quota, but file size, rate, concurrency,
  abuse, provider-budget, and system-safety controls are mandatory.
- Overload queues, degrades, or rejects before acceptance; it never loses
  accepted work or fabricates success.
- Memdot is Apache 2.0 and fully self-hostable with feature parity.

## 5. Core architecture

Target monorepo:

- apps/web — Next.js TypeScript PWA and rich-document UI.
- apps/mcp — thin TypeScript MCP/OAuth protocol edge.
- services/core — FastAPI canonical domain API.
- services/workers — parsing, workflows, projections, sync, export, and deletion.
- services/model-router — isolated model-provider and BYOK egress.
- packages/contracts — generated OpenAPI client, JSON Schemas, and events.
- packages/domain-python — domain policy, provider ports, retrieval, and learning.
- packages/ui — accessible frontend primitives only.
- infra/compose — complete self-host platform.
- infra/hosted — India-first hosted infrastructure.
- tests/benchmark — frozen quality corpus and runners.
- tests/security — cross-account, protocol, injection, deletion, and privacy tests.

Allowed dependency direction:

- UI and MCP depend on generated contracts and Core APIs.
- Core and workers depend on domain policy and provider ports.
- Provider adapters implement inward-facing ports.
- Provider adapters never own authorization, revision truth, public IDs,
  deletion truth, proposals, or learner evidence.

Forbidden shortcuts:

- Web or MCP querying PostgreSQL, object storage, Tex, or model vendors directly.
- Provider IDs becoming public IDs or canonical foreign keys.
- Permissions implemented in prompts.
- Source truth stored only in Tex or vector indexes.
- Documents flattened to Markdown as canonical data.
- Silent last-write-wins for documents or Notion.
- Model confidence treated as learner mastery.
- AI output directly mutating canonical state.
- User content placed in telemetry for debugging.

## 6. Canonical data and truth

- PostgreSQL is canonical for identity, tenancy, authorization, Spaces, sources,
  immutable revisions, documents, memory, conversations, learner events,
  proposals, conflicts, receipts, jobs, outbox, idempotency, deletion, and audit
  metadata.
- Immutable object storage is canonical for original files, exact connector
  snapshots, raw parser artifacts, rendered pages, assets, and exports.
- Tex and local semantic indexes are rebuildable projections.
- Canonical mutations and outbox events commit in one PostgreSQL transaction.
- Every account-owned table has account_id and FORCE RLS.
- Every Space-owned record also has space_id.
- Runtime roles have no BYPASSRLS.
- Worker jobs carry immutable signed authorization snapshots.
- Revisions and learner events are immutable or append-only.
- Corrections use new revisions or compensating events.

Truth classes remain distinct:

- source assertion;
- user assertion;
- external knowledge;
- derived proposal;
- approved derived memory;
- learner evidence;
- system metadata.

Retrieval rank or model confidence cannot change truth class.

## 7. Retrieval and context

- Candidate lanes include exact, temporal, graph, local semantic, and optional
  Tex semantic retrieval.
- Fusion and reranking never change authorization or truth.
- Every candidate is rejoined to canonical PostgreSQL records under RLS.
- Unknown, stale, deleted, retracted, Private-Space, cross-account,
  unauthorized, and wrong-edition candidates are rejected.
- Historical/as-of requests are explicit; default context uses current eligible
  evidence.
- Context receipts record scope, evidence, versions, conflicts, routes,
  omissions, degraded state, and budget decisions.
- Receipts do not store chain-of-thought.
- Every returned citation uses a stable canonical ID, immutable revision,
  locator, and absolute first-party URL that reauthorizes when opened.
- Tex outage falls back to PostgreSQL exact/version/graph plus pgvector and local
  reranking without changing security, citation, receipt, or deletion behavior.

## 8. Learning integrity

- Learning Spaces contain courses, units, objectives, concepts, prerequisites,
  and source coverage.
- Suggested curriculum nodes and edges are not confirmed truth.
- Unconfirmed prerequisites cannot block progression.
- Assessment items and rubrics are versioned and source-anchored.
- Answers and rubrics remain sealed before submission or explicit reveal.
- Confidence is captured before feedback.
- Learner events are append-only and replayable.
- Evidence Twin and FSRS are derived projections.
- Revealed, substantively hinted, post-feedback, ungradable, low-confidence
  provisional, conversation-derived, or otherwise ineligible events cannot raise
  demonstrated learning.
- Offline review events remain provisional until idempotent server
  acknowledgement.
- The north star is source-grounded delayed success on novel eligible items, not
  chat volume, time spent, streaks, or generated-card count.

## 9. External interfaces

Frozen MCP tools:

- search({query})
- fetch({id})
- prepare_context(...)
- propose_memory(...)
- record_interaction(...)

Frozen scopes:

- memdot.memory.read — the complete eligible non-private account across current
  and future non-private Spaces.
- memdot.memory.propose — create pending memory proposals only.
- memdot.interaction.record — append explicitly supplied interaction turns.

MCP invariants:

- search and fetch maintain OpenAI company-knowledge-compatible shapes.
- Returned URLs are absolute, user-openable, and reauthorized.
- Private Spaces, pending proposals, incomplete attempts, sealed answers,
  credentials, and secrets remain excluded.
- record_interaction records completeness and never changes learner evidence.
- Revocation takes effect before the next request.

REST baseline:

- /api/v1 routes;
- generated OpenAPI contracts;
- application/problem+json errors;
- signed cursor pagination;
- idempotency keys on writes;
- durable 202 jobs for long work;
- direct presigned file transfers;
- reauthorization on fetch and lifecycle operations.

## 10. Notion boundary

- Selected pages outside the dedicated Memdot root sync inbound only.
- Memdot never modifies those source pages.
- Approved Memdot-authored documents under the dedicated root may sync in both
  directions.
- Connector snapshots create deterministic source revisions.
- Expiring assets are copied into immutable object storage.
- Concurrent changes create an explicit base/Notion/Memdot conflict.
- Sync pauses only the affected item.
- Resolution is Keep Notion, Keep Memdot, or reviewed merge.
- Silent last-write-wins is forbidden.
- Production completion requires a live authorized Notion test workspace.

## 11. Privacy, deletion, and offline boundary

- User content persists until explicit deletion.
- Deletion immediately removes eligibility and revokes affected sessions, grants,
  integrations, and keys.
- Durable purge covers PostgreSQL content, objects, exports, connector mappings,
  local indexes, Tex, caches, and derived projections.
- Live purge target is seven days.
- Encrypted backup expiry target is 35 days.
- Content-free deletion tombstones replay before restored data is served or
  reprojected.
- Export includes portable canonical content, originals, history, documents,
  approved memory, conversations/completeness, course graph, learner events,
  citations, hashes, and warnings.
- Offline v1 is limited to explicitly pinned reading and a seven-day review
  pack.
- General offline document editing, Ask, imports, sync, MCP, settings/security
  changes, and new test generation are disabled.
- Offline content is encrypted and partitioned by account and cleared on logout
  or account switch.

## 12. Deployment and operations

Hosted:

- Content-bearing services and managed inference run in GCP Mumbai
  asia-south1.
- Delhi asia-south2 holds encrypted disaster-recovery backups only.
- Hosted identity uses Google through the OIDC broker.
- Hosted secrets use Cloud KMS and Secret Manager.
- Content-bearing resources are restricted to approved India locations.

Self-hosted:

- Complete Docker Compose profile.
- Caddy, web, API, MCP, workers, model router, Hatchet, PostgreSQL and pgvector,
  SeaweedFS, Keycloak, OpenBao, and observability.
- Tex disabled by default.
- Telemetry export off by default.
- Local retrieval and a local or explicitly configured model endpoint supported.

Operational targets:

- MCP search p95 at most 1.5 seconds.
- MCP fetch p95 at most 500 milliseconds.
- Context compilation p95 at most 3 seconds excluding generation.
- Accepted-write response p95 at most 750 milliseconds.
- Hosted beta availability at least 99.5 percent.
- Projection lag p95 at most five minutes.
- Deletion authorization revocation at most one minute.
- RPO at most 15 minutes and RTO at most four hours.
- Zero unauthorized or Private-Space candidate output.

## 13. Phase order

1. Repository foundation.
2. Self-host/local platform.
3. Canonical ledger, identity, and authorization.
4. Core API, durable work, and object storage.
5. Ingestion and parsing.
6. Documents, memory, conflicts, and proposals.
7. Retrieval, context, model routing, and Tex fallback.
8. Learning backend.
9. MCP, external AI, and conversations.
10. Notion, export, deletion, and restore.
11. Security, observability, deployment, and evaluation.
12. Frontend foundation.
13. General Memory frontend.
14. Learning and integrations frontend.
15. Release candidate and beta readiness.

Backend, database, security, infrastructure, integrations, lifecycle, and
evaluation foundations are completed before product frontend implementation
begins in Phase 12.

## 14. Current execution pointer

- Active phase: Phase 3 — owner-authorized; implementation not started.
- Builder prompt: supplied by Codex in the Phase 3 owner handoff.
- Detailed checklist: IMPLEMENTATION_TRACKER.md Phase 3.
- Current phase report: none for Phase 3.
- Current Codex verdict: PASS for Phases 1 and 2.
- Current accepted implementation: Phase 2 self-host platform in the commit recording this transition.
- Phase 3 baseline is the accepted Phase 2 commit created with this transition.
- Verified commands: see AGENTS.md and docs/ai/CODEBASE_CONTEXT_MAP.md.
- Phase 3 is authorized. Phase 4 remains unauthorized.

## 15. Context maintenance

Update this file in the same accepted phase whenever:

- verified repository paths or commands change;
- a phase starts, completes, fails, or becomes blocked;
- a component, database table, contract, event, or provider changes ownership;
- a public interface or deployment topology changes;
- a new invariant or approved ADR changes execution;
- a phase report or Codex verdict changes current state.

Never erase historical requirements to make current code appear compliant.
