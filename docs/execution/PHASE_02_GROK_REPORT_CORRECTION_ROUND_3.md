# GROK PHASE REPORT — PHASE 2 (CORRECTION ROUND 3)

### 1. Repository state

- Phase: 2 — Self-host infrastructure and local developer platform (correction round 3)
- Branch: `main`
- Base / HEAD: `6cea8d556d71667c09b7401f88a33a938f561069` (uncommitted Phase 2 work on top)
- Docker: system `dockerd` via `unix:///var/run/docker.sock` (Docker Desktop not used)
- Pre-existing: Phase 2 candidate tree; Engram containers already stopped before smoke
- git status: see `/tmp/phase2-round3-git-status.txt` (dirty; **no commit performed**)

### 2. Completed scope

- Macro-phase objective: Tex-disabled self-host Compose, secrets/TLS/OIDC, durability and ops smoke.
- Correction round 3 closed Codex FAIL items 1–7 with live `make selfhost-smoke` **exit 0**.
- Explicit non-goals: Phase 3 schema/authz, product domain, commits/push/deploy, paid APIs, Tex.
- Deviations: Hatchet canary uses SDK `0.47.x` against server `v0.55`; status via gRPC `result()` + `asyncio.wait_for` (not ThreadPoolExecutor); compose one-shot ends with `os._exit` only after awaited `exit_gracefully`.

### 3. Traceability

- TRD-DEP-004..008, TRD-SEC-005..007, TRD-OPS-009..013, ADR-0011 (Phase 2 primary).
- Security: OpenBao non-dev Transit, secret scan, config guards, CA-trust TLS docs, smoke isolation.
- Evaluation: local CI-equivalent gates + `make selfhost-smoke`.

### 4. Micro-phase self-checks

| Micro-phase | Result | Notes |
| --- | --- | --- |
| 2.1 Compose topology | PASS | Tex absent; digests; parameterized secrets/tls binds |
| 2.2 Config/secrets/trust | PASS | OpenBao Transit, Keycloak, config guards, secret_scan |
| 2.3 Durability smoke | PASS | Live smoke project `memdot-smoke-20260716024239-1851798` |

Codex round-3 fixes applied:

1. **Hatchet canary** — durable `ops_canary_effect` unique constraint; duplicate submit → `durable_effect_count=1`; accepted-work barrier survives `hatchet-engine` restart; bounded `asyncio.wait_for` timeouts; controlled failure requires `Workflow Errors:` + intentional message; unit tests for effect/timeout/failure/transport.
2. **Truthful readiness** — Core: Postgres `SELECT 1`, OpenBao init/unseal/Transit, authenticated Seaweed S3; Workers: Hatchet TCP; MCP: OIDC discovery (`MCP_OIDC_DISCOVERY_URL`); Web: OIDC **not** required for `/api/health` (documented); telemetry outage does not fail product ready.
3. **Smoke isolation** — `MEMDOT_SECRETS_DIR` / `MEMDOT_TLS_DIR` / `MEMDOT_ENV_FILE`; exclusive flock; operator files byte-identical; BusyBox helper removed (OpenBao image for token read); transit token 0600 from start; bootstrap 0700/0600.
4. **CI cleanup** — `/tmp/memdot-smoke-project-name` + `smoke_project_name.sh` validate `^memdot-smoke-[a-z0-9_-]+$`; never derive from `*-logs` basename.
5. **Docs** — canonical `docs/ops/CONFIG_INVENTORY.md`; compose inventory is a link; removed `OPENBAO_DEV_ROOT_TOKEN_ID`; Hatchet `DATABASE_URL`; `CORE_OPENBAO_TRANSIT_TOKEN_FILE`; restore example `memdot_restore_<unique-id>`.
6. **Review artifacts** — handoff patches under `/tmp`; `.gitignore` for Phase 2 patch names; `probe_scratch/` only `.gitkeep`.
7. **Validation** — lightweight gates + one uninterrupted green smoke.

### 5. Changed-file inventory (high level)

- Infrastructure: `infra/compose/**` (compose binds, scripts, images.lock unchanged BusyBox removal, README, docs pointer)
- Workers canary: `canary_*.py`, `canary_gates.py`, `psycopg`, tests
- Core/MCP/Web readiness: `app.py`, `server.ts`, `health.ts`, `health_probes.py`, settings
- CI: `.github/workflows/ci.yml`, `smoke_project_name.sh`, infra tests
- Docs: `CONTEXT.md`, `IMPLEMENTATION_TRACKER.md`, `docs/ops/CONFIG_INVENTORY.md`, this report

Secrets under `infra/compose/secrets/` and `tls/` remain gitignored operator material.

### 6. Data and compatibility impact

- No product schema migrations.
- `memdot_ops` gains `ops_canary_effect` / `ops_canary_barrier` (also created at runtime by canary).
- Public MCP signatures unchanged.
- Compose bind roots overridable without rewriting operator files.

### 7. Validation evidence

Lightweight (host):

- `make format-check` — PASS
- `make lint` / `make typecheck` / `make test` (77 pytest) / `make contracts` ×2 (zero generated diff) / `make docs-validate` / `make build` / `make compose-config` / `bash scripts/secret_scan.sh` / `./scripts/check_whitespace.sh` / `git diff --check` — PASS
- Node engine warning: host Node v26 vs pin `>=22 <23` (informational)

Live smoke (local dockerd), project `memdot-smoke-20260716024239-1851798`:

```text
durable_effect_count=1 duplicate_accepted=True
idempotent_effect_ok=true
controlled_failure_detected=true terminal_state=FAILED
timeout_path_detected=true reason=listener_timeout
accepted_work_restart_ok=true
durable_effect_count=1
hatchet_canary_complete=true
seaweed_durability_ok
core_readiness_degraded dependency=postgres|seaweedfs|openbao
workers_readiness_degraded dependency=hatchet
mcp_readiness_degraded dependency=oidc
telemetry_outage_product_readiness_ok
dependency_failure_recovery_ok
selfhost_smoke_passed project=memdot-smoke-20260716024239-1851798
operator_files_byte_identical=true
```

Log: `/tmp/memdot-selfhost-smoke-round3.log`
Complete patch: `/tmp/PHASE_02_CANDIDATE_ROUND3.patch`
Untracked inventory: `/tmp/phase2-round3-untracked.txt`
git status: `/tmp/phase2-round3-git-status.txt`
Patch apply verify: applies cleanly to `6cea8d5`; candidate files byte-identical (0 mismatches).

### 8. Security and privacy impact

- OpenBao file storage (not `-dev`); root/unseal bootstrap-only; app Transit least-privilege via file token.
- Smoke never rewrites operator secrets/TLS; isolated runtime dir removed after run.
- No real user content; synthetic fixtures only.
- Telemetry export disabled in smoke `.env`.

### 9. Exit gate / limitations / stop

- Phase 2 exit-gate items for smoke/gates/report: checked after live evidence.
- Still open: **Codex PASS**, **owner commit authorization**, Phase 3 start.
- Limitation: `migration_job=N/A` in smoke (entrypoint present; product migrations not Phase 2).
- Limitation: compose canary one-shot uses `os._exit` after graceful worker shutdown so the process returns.
- **No commit, push, merge, deploy, Phase 3 work, or unauthorized external actions performed.**

### 10. Request to Codex

Please re-audit Phase 2 correction round 3 against this report, `/tmp/PHASE_02_CANDIDATE_ROUND3.patch`, untracked inventory, and `/tmp/memdot-selfhost-smoke-round3.log`. Return exactly one verdict: PASS / FAIL — CORRECTIONS REQUIRED / BLOCKED — OWNER DECISION REQUIRED.
