# Prompt for Grok — Implement Memdot Phase 1

Copy everything below this line into Grok in Cursor.

---

You are the implementation builder for Memdot Phase 1.

Your task is to implement the complete Phase 1 — Repository foundation and
production-grade monorepo structure — across all four micro-phases. Do not stop
for Codex review between micro-phases. At each micro-phase boundary, inspect your
own logic, run its validations, fix every failure, record the evidence, and then
continue. Stop and report only after the complete Phase 1 exit gate passes, or
when a genuine blocker requires an owner decision or unsafe external action.

Tauqueer is the owner. Codex will review the complete Phase 1 diff after your
final report. You are not authorized to commit, push, merge, deploy, rotate
credentials, create paid resources, or mutate production/third-party data.

## A. Mandatory reading before editing

Read these files completely in this order:

1. AGENTS.md
2. CONTEXT.md
3. IMPLEMENTATION_PLAN.md
4. IMPLEMENTATION_TRACKER.md sections 1, 2, 3, and Phase 1
5. docs/README.md
6. docs/ai/CODEBASE_CONTEXT_MAP.md sections 1, 2, 3, 8, 9, 11, and 12
7. docs/technical/TRD.md sections 1, 2, 12, 14, and 16
8. docs/technical/SYSTEM_ARCHITECTURE.md sections 2, 4, 7, 17, and 20
9. docs/adr/0011-apache-2-and-self-host-parity.md
10. docs/technical/SECURITY_PRIVACY_THREAT_MODEL.md sections 3, 8, 10, and 12
11. docs/technical/EVALUATION_RELEASE_GATES.md sections 1, 9, 10, 11, 12, and 13
12. docs/execution/PHASE_REPORT_TEMPLATE.md

Do not treat target paths or commands as implemented merely because the
documents name them.

## B. Initial repository inspection

Before editing:

1. Print the current working directory.
2. List the current repository files.
3. Run git rev-parse --is-inside-work-tree and report the result.
4. If Git exists, report branch, HEAD, git status --short, and pre-existing
   changes.
5. If Git does not exist, initialize it with main as the default branch. Do not
   create a commit.
6. Re-run git status --short.
7. Record the baseline file inventory and do not overwrite or discard the
   founding documentation.
8. Check installed Node, pnpm, Python, uv, Docker, Docker Compose, and Git
   versions.
9. If a required tool is absent, use the least invasive reproducible
   installation route available to this development environment. Do not alter
   system-wide state or install prerelease versions without reporting why.
10. Never expose environment secrets in terminal output.

## C. Locked Phase 1 scope

Implement only repository foundation, skeletons, contracts tooling, CI, and
verified documentation.

Do not implement:

- product routes or screens;
- database domain tables or migrations;
- RLS policies;
- authentication behavior;
- ingestion;
- rich-document nodes or editor behavior;
- memory;
- retrieval;
- learning;
- MCP tools;
- Notion;
- deletion/export workflows;
- hosted infrastructure;
- full Compose topology;
- provider/model integration.

Minimal health/readiness behavior and contract-generation fixtures are allowed
only to prove the scaffold.

## D. Technical baseline for Phase 1

Use these defaults unless actual repository or platform evidence makes one
impossible. If a default must change, document the evidence and effect in the
final report.

- One pnpm workspace for TypeScript projects.
- One uv workspace for Python projects.
- A thin root command surface that delegates to pnpm and uv. Prefer a Makefile
  plus owning workspace scripts; do not add a heavy monorepo framework without a
  demonstrated need.
- GitHub Actions for CI.
- Strict TypeScript.
- Python typing strict enough to fail CI on untyped application boundaries.
- Ruff for Python formatting/linting.
- Pyright or mypy as one documented Python type checker; do not maintain two
  competing type configurations.
- ESLint and the framework-supported formatter/linter setup for TypeScript.
- pytest for Python tests and the standard TypeScript test runner selected for
  the workspace.
- openapi-typescript or an equivalently deterministic generator for Core-owned
  OpenAPI types.
- import-linter or an equivalent for Python dependency boundaries.
- ESLint restricted imports or dependency-cruiser for TypeScript dependency
  boundaries.
- Multi-stage non-root Dockerfiles.
- Current supported stable releases only, with exact pins/lockfiles. Verify
  support before pinning; do not invent version numbers.

## E. Micro-phase 1.1 — Repository and workspace scaffold

Complete all of the following:

1. Preserve every existing founding document.
2. Add Apache 2.0 LICENSE.
3. Add a root README that:
   - describes Memdot without claiming implementation;
   - points to CONTEXT.md, IMPLEMENTATION_PLAN.md, IMPLEMENTATION_TRACKER.md,
     AGENTS.md, and docs/README.md;
   - lists only commands verified in this phase;
   - distinguishes scaffold status from product completion.
4. Add CONTRIBUTING.md with branch/diff/test/documentation rules and the
   Tauqueer/Grok/Codex phase workflow.
5. Add ownership metadata that does not invent a GitHub username. An OWNERS.md
   or equivalent architecture ownership map is acceptable. Do not create a fake
   CODEOWNERS identity.
6. Add .editorconfig, .gitattributes, a comprehensive .gitignore, and safe
   environment-example conventions.
7. Create these real ownership boundaries:
   - apps/web
   - apps/mcp
   - services/core
   - services/workers
   - services/model-router
   - packages/contracts
   - packages/domain-python
   - packages/ui
   - infra/compose
   - infra/hosted
   - tests/benchmark
   - tests/security
8. Add pinned toolchain files and deterministic lockfiles.
9. Configure the pnpm and uv workspaces.
10. Add thin root commands for bootstrap, format, lint, type-check, unit test,
    contract validation, documentation validation, build, and clean verification.
11. Document the allowed dependency direction.
12. Do not add domain behavior merely to make a directory non-empty.

### Micro-phase 1.1 self-check

Run and fix:

- clean dependency bootstrap from the declared manifests;
- workspace/package discovery;
- lockfile consistency;
- formatting of scaffold/configuration files;
- repository secret scan if the selected local tool is available;
- git diff --check.

Record commands, exit codes, relevant raw output, and failures fixed. Continue to
Micro-phase 1.2 only after this self-check passes.

## F. Micro-phase 1.2 — Service and package skeletons

Complete all of the following:

1. Scaffold apps/web as a TypeScript Next.js PWA-capable application shell with
   no product screens. A minimal health route is allowed.
2. Scaffold apps/mcp as a thin TypeScript service with health/readiness only.
   It must not query or import PostgreSQL, object storage, Tex, or model SDKs.
3. Scaffold services/core as FastAPI with typed settings and liveness/readiness
   endpoints only.
4. Scaffold services/workers with typed settings and an appropriate minimal
   process-health mechanism. Do not implement workflows.
5. Scaffold services/model-router with typed settings and liveness/readiness
   only. Do not implement model providers.
6. Scaffold packages/contracts as generated-contract ownership.
7. Scaffold packages/domain-python as domain types and inward-facing provider
   port ownership without business logic.
8. Scaffold packages/ui as accessible frontend primitive ownership without
   product UI.
9. Add unit tests for every health/readiness boundary and settings failure.
10. Add dependency-boundary enforcement proving:
    - web and MCP cannot import database or provider adapters;
    - MCP cannot import Core internals;
    - workers cannot import UI;
    - provider/adapters cannot be imported into domain policy;
    - TypeScript does not reimplement Python domain policy.
11. Add multi-stage minimal Dockerfiles that:
    - run as a non-root user;
    - copy only required runtime artifacts;
    - have explicit health checks where appropriate;
    - do not contain credentials;
    - do not run destructive migrations;
    - can build without the future Phase 2 Compose topology.

### Micro-phase 1.2 self-check

Run and fix:

- TypeScript build and type-check for web, MCP, contracts, and UI;
- Python import, type-check, and unit tests for Core, workers, model router, and
  domain package;
- dependency-boundary positive and deliberately failing fixture tests;
- every container build;
- non-root container inspection;
- health/readiness smoke tests;
- git diff --check.

Continue to Micro-phase 1.3 only after this self-check passes.

## G. Micro-phase 1.3 — Contract and schema toolchain

Complete all of the following:

1. Make FastAPI Core the canonical OpenAPI owner.
2. Generate TypeScript OpenAPI types/client artifacts into packages/contracts.
3. Add a deterministic command that regenerates contracts and fails when
   committed generated output is stale.
4. Establish versioned JSON Schema generation and validation infrastructure for:
   - public resource envelopes;
   - application/problem+json;
   - future MemdotDocument;
   - provider ports;
   - export manifests.
5. Do not implement the full MemdotDocument node model in this phase. Establish
   the versioning/generation mechanism and a minimal non-product fixture; the
   complete schema belongs to Phase 6.
6. Establish versioned event-schema layout and compatibility policy using test
   fixtures only. Do not invent production domain events prematurely.
7. Establish stable error-code registry ownership without filling it with future
   feature errors.
8. Add serialization-equivalence tests across Python, generated OpenAPI,
   TypeScript, JSON Schema, and event fixtures.
9. Add backward-compatibility tests for additive changes and major-version
   rejection.
10. Generate twice and prove deterministic zero-diff output.

### Micro-phase 1.3 self-check

Run and fix:

- OpenAPI generation;
- TypeScript generation and compile;
- JSON Schema validation;
- event-schema validation;
- backward-compatibility fixtures;
- Python/TypeScript serialization-equivalence tests;
- two consecutive generations with no second diff;
- stale-generated-file negative test;
- git diff --check.

Continue to Micro-phase 1.4 only after this self-check passes.

## H. Micro-phase 1.4 — CI, hygiene, and verified documentation

Complete all of the following:

1. Add GitHub Actions CI for:
   - repository formatting;
   - TypeScript lint/type-check/test/build;
   - Python format/lint/type-check/test;
   - dependency-boundary tests;
   - OpenAPI/JSON Schema/event compatibility;
   - generated-file freshness;
   - documentation local-link validation;
   - Mermaid render validation;
   - secret scanning;
   - dependency review;
   - container builds;
   - git diff whitespace checks.
2. Fail CI on:
   - focused or disabled tests committed accidentally;
   - unexplained skips;
   - stale generated files;
   - dependency-boundary violations;
   - committed secrets;
   - broken local links;
   - invalid Mermaid;
   - container build failure.
3. Do not pretend database migration validation is meaningful before Phase 3.
   Establish the CI seam and document it as not applicable until migrations
   exist; do not add fake migrations.
4. Add deterministic, content-safe fixture rules.
5. Add documentation validation scripts that cover AGENTS.md, CONTEXT.md,
   implementation documents, docs, ADR links, requirement references, and
   Mermaid diagrams.
6. Update AGENTS.md with actual verified commands and paths.
7. Update docs/ai/CODEBASE_CONTEXT_MAP.md:
   - change target paths to verified paths where now real;
   - retain target labels for unimplemented subsystems;
   - record actual dependency enforcement;
   - record only tested commands.
8. Update CONTEXT.md current state to Phase 1 candidate implemented, pending
   Codex audit.
9. Update docs/README.md status without claiming product behavior.
10. Ensure IMPLEMENTATION_PLAN.md and IMPLEMENTATION_TRACKER.md remain consistent
    with the phase-level review workflow.

### Micro-phase 1.4 self-check

Run and fix the complete local equivalent of CI:

- clean bootstrap;
- format check;
- TypeScript lint, type-check, tests, and builds;
- Python lint, type-check, tests, and imports;
- dependency-boundary tests;
- contract/schema generation and compatibility;
- generated-file freshness;
- documentation links and Mermaid rendering;
- secret scan;
- every Dockerfile build;
- health smoke tests;
- git diff --check.

Continue to the Phase 1 exit gate only after this self-check passes.

## I. Phase 1 exit gate

You must prove all of these:

1. A clean environment can install dependencies, discover every workspace,
   build every skeleton, and run documented commands.
2. All intended ownership paths exist and match the architecture.
3. Dependency-direction violations fail automatically.
4. Core-owned generated contracts are deterministic.
5. Python and TypeScript serialization fixtures agree.
6. Containers build, run as non-root, contain no credentials, and pass
   health/readiness smoke tests.
7. CI-equivalent validation passes without ignored failures, unexplained skips,
   or unexplained warnings.
8. Documentation local links and Mermaid rendering pass.
9. AGENTS.md, CONTEXT.md, docs/README.md, and Codebase Context Map describe the
   actual Phase 1 candidate state and verified commands.
10. No product/domain functionality is falsely claimed or implemented outside
    Phase 1.
11. git diff --check passes.
12. No unauthorized commit, push, merge, deploy, credential rotation, paid
    resource, or external/production data mutation occurred.

If any gate fails, fix it and rerun the affected micro-check plus the complete
Phase 1 gate. Do not send a success report with failing or skipped required
checks.

## J. Blocker rules

Stop before Phase 1 completion only if:

- the founding documents materially contradict each other;
- a required tool cannot be installed safely;
- a choice would change a locked architecture or product contract;
- an owner identity or credential is required;
- an action would create a paid/external resource;
- an action would mutate production or third-party data;
- an environment failure remains after bounded diagnosis and prevents required
  validation.

When blocked, report:

- exact micro-phase;
- exact command/error;
- what you tried;
- why safe progress cannot continue;
- smallest owner decision or environment change needed.

Do not silently skip the blocked check.

## K. Final report

After the entire Phase 1 gate passes, stop implementation and produce one report
using docs/execution/PHASE_REPORT_TEMPLATE.md.

The report heading must be:

GROK PHASE REPORT — PHASE 1

The report must include:

- baseline and final repository state;
- all four micro-phase self-check summaries;
- complete changed-file inventory;
- exact requirement/ADR/security/evaluation traceability;
- toolchain/version choices and why;
- all verified root commands;
- all unedited relevant terminal output and exit codes;
- test totals, skips, coverage, warnings, and failures fixed;
- contract generation and deterministic second-run evidence;
- dependency-boundary evidence;
- Docker build/non-root/health evidence;
- documentation link and Mermaid evidence;
- secret-scan evidence;
- git status --short;
- git diff --stat;
- git diff --check;
- the complete reviewable diff or patch;
- known limitations and work intentionally deferred to Phase 2+;
- authority confirmation.

Do not commit. Wait for Tauqueer to bring the report and diff to Codex for the
Phase 1 audit.

---
