# GROK PHASE REPORT — PHASE 2 (CORRECTION ROUND 2)

### 1. Repository state

- Phase: 2 — Self-host infrastructure and local developer platform (correction round 2)
- Branch: `main`
- Base / HEAD: `6cea8d556d71667c09b7401f88a33a938f561069` (uncommitted Phase 2 work on top)
- Docker: system `dockerd` via `unix:///var/run/docker.sock` (Docker Desktop not used)
- Pre-existing: Phase 2 candidate tree; Engram containers stopped for RAM during smoke
- git status: see `/tmp/phase2-git-status.txt` (dirty; **no commit performed**)

### 2. Completed scope

- Macro-phase objective: Tex-disabled self-host Compose, secrets/TLS/OIDC, durability and ops smoke.
- Correction round 2 closed Codex FAIL items 1–10 with live `make selfhost-smoke` **exit 0**.
- Explicit non-goals: Phase 3 schema/authz, product domain, commits/push/deploy, paid APIs, Tex.
- Deviations: Hatchet canary uses SDK `0.47.x` (not 1.x) against server `v0.55`; status via gRPC `sync_result` (JWT REST URL is host-loopback).

### 3. Traceability

- TRD-DEP-004..008, TRD-SEC-005..007, TRD-OPS-009..013, ADR-0011 (Phase 2 primary).
- Security: OpenBao non-dev Transit, secret scan, config guards, CA-trust TLS docs.
- Evaluation: local CI-equivalent gates + `make selfhost-smoke`.

### 4. Micro-phase self-checks

| Micro-phase | Result | Notes |
| --- | --- | --- |
| 2.1 Compose topology | PASS | Tex absent; digests; internal nets; health deps |
| 2.2 Config/secrets/trust | PASS | OpenBao Transit, Keycloak, Caddy CA trust docs, config guards, secret_scan |
| 2.3 Durability smoke | PASS | Live smoke project `memdot-smoke-20260715200737-1686882` |

Codex round-2 fixes applied:

1. Tracker honesty restored then re-checked only after live smoke.
2. `secret_scan.sh` + patterns file + positive/negative tests.
3. Real Hatchet workflow canary (register/run SUCCEEDED + controlled FAILED + post-engine-restart).
4. One-shot retry removes failed containers before recreate.
5. PostgreSQL restore only to `memdot_restore_*` disposable DBs.
6. OpenBao bootstrap `0700`/`0600`; transit token Core uid `10001`.
7. Core `/health/ready` degrades on postgres/openbao outage; dependency smoke proves it.
8. Smoke freshness labels + operator `.env`/secrets/tls backup/restore via root helper.
9. TLS docs trust **CA**; CONFIG_INVENTORY corrected; URL/origin/plaintext guards.
10. Lightweight gates + uninterrupted green smoke on local dockerd.

### 5. Changed-file inventory (high level)

- Infrastructure: `infra/compose/**` (compose, scripts, config, dashboards, images.lock, README)
- Workers canary: `services/workers/.../canary_*.py`, `hatchet-sdk>=0.47.1,<1`
- Core readiness: `services/core/src/memdot_core/app.py`
- Domain config guards / OpenBao adapter / secret scan scripts + tests
- Docs: `CONTEXT.md`, `IMPLEMENTATION_TRACKER.md`, `docs/ops/*`, `docs/README.md`

Secrets under `infra/compose/secrets/` and `tls/` remain gitignored operator material.

### 6. Data and compatibility impact

- No product schema migrations.
- Hatchet DB migrations run only via `hatchet-migrate` one-shot.
- Public MCP signatures unchanged.
- Postgres healthcheck now requires `hatchet` + `memdot_ops` DBs (avoids initdb race).

### 7. Validation evidence

Lightweight (host):

- `make format-check` — PASS (after Prettier on touched files)
- `make lint` / `make typecheck` / `make test` (54 pytest) / `make contracts` / `make docs-validate` / `make build` / `make compose-config` / `bash scripts/secret_scan.sh` — PASS
- Node engine warning: host Node v26 vs pin `>=22 <23` (informational)

Live smoke (local dockerd):

```text
selfhost_smoke_passed project=memdot-smoke-20260715200737-1686882
hatchet_canary_complete=true
seaweed_durability_ok
postgres_durability_ok
restore_ok target=memdot_restore_1686882
restart_recovery_ok
dependency_failure_recovery_ok
observability_smoke_ok
SMOKE_EXIT=0
```

Log: `/tmp/memdot-selfhost-smoke.log`
Tracked diff patch: `/tmp/PHASE_02_CANDIDATE.patch`
Untracked file list: `/tmp/phase2-untracked.txt`

### 8. Security and privacy impact

- OpenBao file storage (not `-dev`); root/unseal bootstrap-only; app Transit least-privilege.
- Smoke restores operator secrets/TLS after run (does not leave rematerialized smoke secrets as operator state).
- No real user content; synthetic fixtures only.
- Telemetry export disabled in smoke `.env`.

### 9. Exit gate / limitations / stop

- Phase 2 exit-gate items for smoke/gates/report: checked after live evidence.
- Still open: **Codex PASS**, **owner commit authorization**, Phase 3 start.
- Limitation: `migration_job=N/A` in smoke (entrypoint present; product migrations not Phase 2).
- Limitation: host RAM was tight (~3–8 GiB available); Engram must stay stopped during smoke.
- **No commit, push, merge, deploy, or Phase 3 work performed.**

### 10. Request to Codex

Please re-audit Phase 2 correction round 2 against this report, `/tmp/PHASE_02_CANDIDATE.patch`, untracked inventory, and `/tmp/memdot-selfhost-smoke.log`. Return exactly one verdict: PASS / FAIL — CORRECTIONS REQUIRED / BLOCKED — OWNER DECISION REQUIRED.
