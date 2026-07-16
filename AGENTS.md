# Memdot agent guidance

Before changing anything:

1. Read [docs/README.md](docs/README.md).
2. Read [CONTEXT.md](CONTEXT.md) for verified current state and invariants.
3. Read [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) and work only in the
   active owner-approved delivery wave.
4. Read the active wave and technical phases in
   [IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md).
5. Read [docs/ai/CODEBASE_CONTEXT_MAP.md](docs/ai/CODEBASE_CONTEXT_MAP.md).
6. Read the owning PRD/FSD/TRD requirements and relevant ADRs.
7. Read the security controls and evaluation gates for the affected domain.
8. Inspect actual files and manifests; never infer an implementation or command
   from the target map.

Within an approved delivery wave, Grok completes micro-phases in order and
self-validates each one. Codex reviews once at the wave boundary. Do not request
routine Codex review between micro-phases.

Prompts, correction prompts, consolidated reports, raw logs, candidate patches,
stats, and file inventories are chat or `/tmp` artifacts. Do not add them under
`docs/`. Repository documentation is reserved for durable product, architecture,
security, evaluation, operator, context, and implementation truth.

Grok may use bounded multitask mode. Give parallel tasks exclusive paths and
explicit contracts. Migrations, RLS/auth, public APIs/events, shared Compose/CI,
MemdotDocument, deletion truth, and learner-evidence policy have one writer at a
time. The main task reconciles the combined diff and runs the integrated gate.

Durable invariants:

- PostgreSQL is canonical; Tex and all indexes are rebuildable projections.
- Private spaces are never externally retrievable.
- AI writes and edits are proposals until user approval.
- Every retrieved item has canonical revision and citation provenance.
- External chat capture is best effort and visibly labelled.
- Learning evidence comes from eligible append-only events, not chat activity.
- Self-hosting must work without Tex or paid model APIs.
- Public MCP `search`/`fetch` signatures remain compatibility-safe.
- Documentation and traceability IDs must change with behaviour or architecture.
- Commit, push, merge, deploy, paid resources, credentials, production data, and
  phase transitions remain owner-controlled even after tests pass.

## Full-smoke policy

Before frontend work, only two future full `make selfhost-smoke` runs are
scheduled: Checkpoint A after technical Phase 8 and Checkpoint B after technical
Phase 11. Waves 4, 5, and 7 use focused component/integration gates only. Do not
repeat a successful full smoke during correction unless the correction changes
Compose topology, startup/readiness, networking, TLS/OIDC discovery, secrets,
runtime DB roles/migrations, Hatchet durability, object persistence,
backup/restore/tombstones, telemetry-off boot, or Tex-disabled fallback.

## Verified Phase 1 commands

Inspected and exercised during Phase 1 scaffolding:

```bash
make bootstrap      # pnpm install --frozen-lockfile && uv sync --all-packages --group dev --frozen
make format         # prettier + ruff format/fix
make format-check   # formatting verification
make lint           # ESLint, dependency-cruiser, ruff, import-linter
make typecheck      # tsc + pyright (Python 3.12)
make test           # vitest + pytest (+ boundary/contract suites)
make contracts      # Core OpenAPI -> packages/contracts + schema validation
make docs-validate  # documentation links + Mermaid parse validation
make build          # TypeScript builds + Python import smoke
make containers     # Docker image builds + non-root inspection
make container-smoke # start images and verify health endpoints
make check          # full local CI-equivalent suite
make clean          # remove local caches/artifacts
make workspace-list # discover pnpm and uv workspace members
```

## Verified Phase 2 commands

```bash
make compose-config   # render Compose + policy validation (Tex absent, digests, exposure)
make compose-up       # start Tex-disabled self-host stack (dev overlay, loopback operator ports)
make compose-ps       # service status
make compose-logs     # recent logs
make compose-down     # stop stack; preserves named volumes
make selfhost-smoke   # bounded end-to-end infra smoke (TLS, OIDC, durability, canary)
```

## Verified Phase 3 commands

```bash
make migrate-domain # explicit Alembic upgrade as memdot_migrate
make check-rls      # live RLS registry gate against PostgreSQL
make phase3-gates   # migrate-domain + check-rls + targeted pytest
```

## Verified Phase 4 commands

```bash
make phase4-gates   # Wave 4 focused gate (no full selfhost-smoke)
```

Operator docs: `infra/compose/README.md`. Image digests: `infra/compose/images.lock.yaml`.
Separate DB roles: `memdot_migrate` (owner/BYPASSRLS), `memdot_core` (runtime/NOBYPASSRLS),
`memdot_test_admin` (disposable tests). Secrets: `infra/compose/secrets/db-roles.env.example`.

Package managers: `pnpm@11.5.2`, `uv` with lockfile `uv.lock`.
Node engines: `>=22 <23` (pinned via `.nvmrc` to 22).
Python: `>=3.12`, validated and containerized on **3.12** (`.python-version` 3.12).

Do not invent alternate commands when these exist.
