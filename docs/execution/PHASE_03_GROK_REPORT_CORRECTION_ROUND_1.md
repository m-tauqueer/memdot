# GROK PHASE REPORT — PHASE 3 CORRECTION ROUND 1

## 1. Repository state

- Phase: 3 — Canonical PostgreSQL ledger, tenancy, identity, and authorization
- Branch: `main`
- Base commit: `2c96aa7` ("Build self-host platform and operational safeguards")
- Current HEAD: `2c96aa7` (unchanged; no commit)
- Pre-existing changes: uncommitted Phase 3 candidate preserved and corrected in place
- Codex prior verdict: FAIL — CORRECTIONS REQUIRED
- git status --short: 49 candidate paths (see `PHASE_03_UNTRACKED.txt`) plus handoff artifacts under `docs/execution/PHASE_03_*`

## 2. Completed scope

### Macro-phase objective (unchanged)

PostgreSQL is the enforceable authorization join point with frozen Alembic migrations, tenancy and evidence-ledger schema, protected tenant context, hosted Google / self-host OIDC auth routes, browser sessions, 18+ attestation, live RLS registry gates, and full adversarial matrix coverage.

### Correction round objective

Address every Codex FAIL item from Round 0 without starting Phase 4, without committing, and without marking Codex/owner exit gates complete.

### Explicit non-goals

- Phase 4 Core write path / object storage / Hatchet product workflows
- Claiming Codex PASS or owner authorization
- Committing, pushing, merging, deploying, or rotating production credentials

### Deviations from the original Phase 3 report

- Original report claimed ~37 Phase 3 tests and deferred `make selfhost-smoke`; both corrected.
- Original migration used `Base.metadata.create_all()`; replaced with frozen SQL operations.
- Original tenant context allowed raw `set_config` unlock / migration+admin purposes at runtime; removed.
- Original Caddy `handle_path /api/*` stripped `/api` so public `/api/v1/*` never reached Core; fixed.
- Unsupported “skipped success” migration seam messaging removed; job fails closed when config absent and verifies Alembic head + schema.

## 3. Traceability

- PRD: PRD-CORE-001, PRD-PRIV-001/002, PRD-INT-002
- FSD: FSD-AUTH-001..005, FSD-ONB-001..002
- TRD: TRD-DATA-001..012, TRD-SEC-001, TRD-SEC-013
- ADR: ADR-0002, ADR-0007
- Threat model: cross-account isolation, Private Space exclusion, session fixation/replay, role separation
- Evaluation: Phase 3 live RLS registry + per-table adversarial matrix

## 4. Codex FAIL items → fixes

### 4.1 Database roles and Compose wiring

**FAIL:** Core connected as bootstrap superuser; migration seam printed skipped success; roles/privileges insufficiently separated.

**Fixed:**
- Separate credentials/URLs: `memdot_migrate`, `memdot_core`, `memdot_test_admin` via `db-roles.env` (+ examples)
- Core Compose URL uses `memdot_core` only (`materialize_local_secrets.sh`, `core.env.example`)
- `ensure_db_roles.sh` + `config/postgres/02-app-roles.sh` provision roles; runtime role NOBYPASSRLS, no DDL/ownership, cannot assume migrate/admin
- Migration role owns schema/tables (`memdot_migrate`)
- `migration_job.sh` fails non-zero when migration URL absent; runs Alembic upgrade; verifies head + expected schema (no skipped-success print)
- Self-host smoke rewrites host URLs and asserts Core `current_user=memdot_core`, NOBYPASSRLS, table owner=`memdot_migrate`; Alembic version read via migrate URL
- Tests: `services/core/tests/test_roles.py`

### 4.2 Protected tenant context (TRD-DATA-004)

**FAIL:** Arbitrary runtime `set_config` unlock; migration/admin purposes usable at runtime; enumerable identity/bootstrap policies.

**Fixed:**
- `memdot_begin_tenant_context` / sealed HMAC context / `memdot_rls_ok`; app only calls begin/clear (`db/tenant.py`)
- Runtime rejects `migration`/`admin` purposes (invoker detection via session/role settings, not definer `current_user`)
- Auth seams: `memdot_auth_find_identity`, `memdot_auth_load_session`, provision/bootstrap functions (non-enumerating)
- Malicious tests: forged GUCs, forged actor, invalid purpose, revoked membership/grant, worker misuse → zero rows (`tests/security/test_rls_adversarial.py`)
- Design documented in schema/security ownership docs

### 4.3 Auth and session behavior

**FAIL:** Unsafe session lookup, missing CSRF, caller-selected nonce proof, weak bootstrap, incomplete integration coverage.

**Fixed:**
- Safe session load via `memdot_auth_load_session` (no table enumeration)
- ORM writes flush/commit under sealed tenant context; deps reset after commit
- CSRF on attestation, logout, and session rotate
- Server-issued, stored, hashed, expiring, single-use OIDC state/nonce (`OidcLoginChallenge`); durable replay table
- Malformed cookies → safe 401; session rotation/fixation prevention; recent-auth helper
- Logout/revocation verified on next request; DB-layer one-time concurrency-safe bootstrap
- Pending-attestation hosted identities blocked from product-content writes (DB triggers)
- Public auth routes return `application/problem+json` helpers (full FSD error surface remains Phase 4 boundary where not claimed)
- Integration tests: `services/core/tests/test_auth_routes_integration.py` (callback, attestation confirm/decline, CSRF, reload, malformed cookie, rotation, logout/revocation, recent-auth, nonce/state replay, bootstrap concurrency, hosted non-Google rejection)
- Smoke: Caddy preserves `/api` prefix; Core normalizes `postgres://` → `postgresql+psycopg://`

### 4.4 Freeze and repair schema

**FAIL:** `create_all()` in Alembic; weak structural ownership; fail-open external visibility.

**Fixed:**
- Frozen SQL: `services/core/alembic/versions/20260716_0001_phase3_canonical.sql` executed by revision (no `create_all`)
- Autogeneration/schema-drift + clean-vs-upgraded convergence: `test_schema_drift.py`
- Composite Space FKs / check constraints / UUIDv5 revision id trigger / private-relabel prevention / pending-attestation write blocks / pointer+outbox atomicity / append-only + provenance immutability
- External visibility fail-closed allowlist (not `visibility <> 'private'`)
- Ledger constraint tests expanded

### 4.5 Replace superficial security gates

**FAIL:** File-existence RLS gate; incomplete matrix; no negative controls.

**Fixed:**
- Live `scripts/check_rls_registry.sh`: registry ↔ actual account-owned tables ↔ ENABLE/FORCE RLS ↔ policies ↔ owner ↔ runtime grants ↔ adversarial registration
- Parameterized matrix over every account-owned table (cross-account CRUD, known-ID, FK attachment, cross-Space, missing/forged context, Private Space external, pagination/count, safe errors)
- Negative controls temporarily violate then restore (`test_negative_controls.py`)

### 4.6 CI and documentation

**FAIL:** CI did not migrate against PostgreSQL / run live RLS; docs/test counts inaccurate; exit gates prematurely claimed.

**Fixed:**
- CI Python job: Postgres service + live migrate + `check_rls_registry.sh` + Phase 3 pytest
- Updated `AGENTS.md`, `CONTEXT.md`, tracker Phase 3 label `(Codex FAIL; Round 1 corrections)`, `SCHEMA_OWNERSHIP.md`, `CONFIG_INVENTORY.md`, `CODEBASE_CONTEXT_MAP.md`
- Codex and owner Phase 3 exit gates remain unchecked
- Corrected validation counts in this report (original unsupported claims superseded)

### 4.7 Late smoke blockers fixed during correction validation

1. Host-side migrate URL rewrite (`@postgres` → published port)
2. SQLAlchemy `postgres://` dialect → normalize in Alembic + Core engine
3. Caddy `handle_path /api/*` → `handle /api/*` (preserve OpenAPI `/api/v1/...`)
4. Smoke Alembic version check uses migrate role URL (Core must not need `alembic_version` SELECT)

## 5. Changed-file inventory (grouped)

- **repository/tooling:** `Makefile`, `.github/workflows/ci.yml`, `scripts/migrate_domain.sh`, `scripts/check_rls_registry.sh`, `pyproject.toml`, `uv.lock`
- **application/service:** `services/core/src/memdot_core/{app,settings,deps}.py`, `auth/**`, `db/**`, `alembic/**`
- **package/contract:** `packages/domain-python/.../{ids,tenancy}.py`, OpenAPI generated clients
- **infrastructure:** Compose role scripts, `migration_job.sh`, `selfhost_smoke.sh`, Caddyfile, postgres init/roles, secret examples
- **test/fixture:** `services/core/tests/**`, `tests/security/**`, `tests/support/**`
- **documentation:** `AGENTS.md`, `CONTEXT.md`, `IMPLEMENTATION_TRACKER.md`, `SCHEMA_OWNERSHIP.md`, ops/config map, Codebase Context Map
- **handoff artifacts (excluded from candidate patch content):** `PHASE_03_CANDIDATE.*`, this correction report, original `PHASE_03_GROK_REPORT.md`

## 6. Data and compatibility impact

- Migration head: `20260716_0001`
- Roles: migrate owner + BYPASSRLS for DDL; core DML + NOBYPASSRLS; disposable test admin
- RLS: FORCE RLS + protected-context policies; fail-closed external allowlist
- OpenAPI: `/api/v1/auth/*` (+ meta)
- Backward compatibility: Phase 2 migration placeholder replaced by explicit Alembic; Tex still absent

## 7. Validation evidence

### Focused gates (required sequence)

| Command | Exit | Evidence |
|---|---|---|
| `make format-check` | 0 | Prettier + ruff format/check passed |
| `make lint` | 0 | ESLint/depcruise/ruff/import-linter; contracts 4 kept |
| `make typecheck` | 0 | tsc + pyright 0 errors |
| Frozen migration + schema drift + clean/upgraded | 0 | `pytest … test_schema_drift.py` (3) + migrate head |
| Role/privilege tests | 0 | `test_roles.py` (3) |
| Auth route integration | 0 | `test_auth_routes_integration.py` |
| Full RLS matrix + registry | 0 | `test_rls_adversarial.py` (42); `check_rls_registry.sh` → `rls_registry_ok tables=34` |
| Structural ledger constraints | 0 | `test_ledger_constraints.py` |
| `make contracts` | 0 | OpenAPI generate + schema validation |
| `make docs-validate` | 0 | 41 docs; 15 Mermaid diagrams |
| `bash scripts/secret_scan.sh` | 0 | passed |
| `git diff --check` (candidate index) | 0 | trailing whitespace stripped from frozen SQL |

Phase 3 targeted suite:

```text
uv run pytest services/core/tests tests/security -q
# 89 tests collected; 89 passed (0 failed, 0 skipped)
```

(Original report’s “37 passed” claim is superseded.)

### Final selfhost-smoke (exactly one green run after focused gates)

```bash
UV_CACHE_DIR=/tmp/memdot-uv-cache make selfhost-smoke
# exit 0
```

Relevant lines from `/tmp/selfhost-smoke-final.txt`:

```text
migration_job=ok
head=20260716_0001 (head)
head=20260716_0001
schema_ok
core_runtime_role_ok
auth_session_endpoint_ok status=401
selfhost_smoke_passed project=memdot-smoke-20260716053422-2135868
```

Smoke proves: migration applied (not skipped), Alembic at head, Core connects as `memdot_core` (not superuser/table owner; no BYPASSRLS), auth session endpoint works through stack (401 unauthenticated), Phase 2 durability/recovery/observability still green.

### Handoff regeneration verify

- Patch: `docs/execution/PHASE_03_CANDIDATE.patch` (64 files, applies cleanly to `2c96aa7`)
- Stat: `docs/execution/PHASE_03_CANDIDATE.stat.txt`
- Inventory: `docs/execution/PHASE_03_UNTRACKED.txt` (49 lines matching `git status --short` candidate paths)
- Reconstruction: worktree apply → **0 byte mismatches** vs working tree for all patched paths
- Handoff artifacts and ignored secrets excluded from patch content

## 8. Phase 3 exit gate

Tracker Grok-side items remain candidate claims pending Codex re-audit. Codex and owner gates are **not** marked complete:

| Gate | Status |
|---|---|
| Migrations clean + upgraded converge | EVIDENCE GREEN — pending Codex |
| PostgreSQL enforceable authorization join point | EVIDENCE GREEN — pending Codex |
| Hosted Google + self-host OIDC + 18+ + sessions/CSRF | EVIDENCE GREEN — pending Codex |
| FORCE RLS + adversarial suite | EVIDENCE GREEN — pending Codex |
| Immutable/append-only structural enforcement | EVIDENCE GREEN — pending Codex |
| Auth claims separate from product authorization | EVIDENCE GREEN — pending Codex |
| Grok consolidated report | THIS DOCUMENT |
| Codex Phase 3 audit PASS | **OPEN** |
| Owner authorize commit + Phase 4 | **OPEN** |

## 9. Security and privacy

- FORCE RLS on 34 account-owned tables; runtime role cannot DDL/BYPASSRLS/own tables
- Protected sealed context; forged GUCs cannot unlock foreign tenant rows
- Private Spaces fail-closed for external purpose
- Session/OIDC secrets hashed; single-use state/nonce; CSRF on state-changing cookie routes
- No runtime secrets/TLS materials staged into git

## 10. Diff evidence

- `git status --short`: see `PHASE_03_UNTRACKED.txt` (+ handoff `PHASE_03_*` files)
- `git diff --stat`: `PHASE_03_CANDIDATE.stat.txt` (64 files, +6459 / −130)
- Complete patch: `PHASE_03_CANDIDATE.patch`
- HEAD remains `2c96aa7`

## 11. Known limitations and blockers

- Downgrade migration intentionally not automated (owner-controlled)
- Full hosted Google live IdP end-to-end against production Google remains fixture/stubbed at OIDC adapter boundary where tests inject tokens
- Complete FSD `application/problem+json` field-pointer surface for all Core APIs is Phase 4; auth routes use safe problem+json helpers now
- No unresolved blocker requiring owner decision for this correction round

## 12. Authority confirmation

- No unauthorized commit
- No unauthorized push or merge
- No unauthorized deployment
- No unauthorized credential rotation
- No unauthorized paid/external resource creation
- No unauthorized production or third-party data mutation
- Phase 4 not started

## 13. Requested Codex action

Re-audit the Phase 3 correction-round candidate at base `2c96aa7` against this report and:

- `docs/execution/PHASE_03_CANDIDATE.patch`
- `docs/execution/PHASE_03_CANDIDATE.stat.txt`
- `docs/execution/PHASE_03_UNTRACKED.txt`

Return exactly one verdict:

- PASS
- FAIL — CORRECTIONS REQUIRED
- BLOCKED — OWNER DECISION REQUIRED
