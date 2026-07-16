# GROK PHASE REPORT — PHASE 3

## 1. Repository state

- Phase: 3 — Canonical PostgreSQL ledger, tenancy, identity, and authorization
- Branch: `main`
- Base commit: `2c96aa7` ("Build self-host platform and operational safeguards")
- Current HEAD: `2c96aa7` (uncommitted candidate)
- Pre-existing changes: none
- git status --short: 46 changed/untracked implementation files (see `PHASE_03_UNTRACKED.txt`)

## 2. Completed scope

### Macro-phase objective

PostgreSQL is the enforceable authorization join point with Alembic migrations, tenancy and evidence-ledger schema, hosted Google/self-host OIDC auth routes, browser sessions, 18+ attestation, and adversarial RLS coverage.

### Completed micro-phases

| Micro-phase | Summary |
|---|---|
| 3.1 | SQLAlchemy 2.x + Alembic; roles (`memdot_migrate`, `memdot_core`, `memdot_test_admin`); tenancy tables; composite FKs; transaction GUCs; FORCE RLS |
| 3.2 | Evidence-ledger foundations (sources, revisions, documents, provenance, truth classes, conflicts, proposals, conversations, audit, pointers, outbox/idempotency/jobs/projections); immutability/append-only triggers |
| 3.3 | OIDC issuer adapter; Google-only hosted gate; self-host bootstrap; auth API routes; sessions/CSRF; 18+ attestation |
| 3.4 | Cross-account/Private Space adversarial suite; runtime-role tests; RLS registry CI gate; negative controls |

### Explicit non-goals

- Phase 4 Core write path, object storage, Hatchet workflows
- Product frontend screens
- Full MCP/OAuth external-client product grants (foundations only)
- `make selfhost-smoke` re-run (migration seam updated; full stack smoke deferred to Codex/owner)

## 3. Traceability

- PRD: PRD-CORE-001, PRD-PRIV-001/002, PRD-INT-002
- FSD: FSD-AUTH-001..005, FSD-ONB-001..002
- TRD: TRD-DATA-001..012, TRD-SEC-001, TRD-SEC-013
- ADR: ADR-0002, ADR-0007
- Threat model: cross-account isolation, Private Space exclusion, session fixation/replay controls
- Evaluation: Phase 3 cross-account matrix (security suite)

## 4. Micro-phase self-checks

### 3.1 — Migration framework and tenancy schema

- Logic: Alembic revision `20260716_0001`; 34 account-owned tables; UUIDv7/v5 helpers; tenant GUCs; migration job replaces Phase 2 placeholder
- Validation: `pytest services/core/tests/test_migrations.py services/core/tests/test_ids.py -q` → 9 passed
- Failures fixed: reserved `user` table quoting; unique constraint naming; URL password masking in fixtures

### 3.2 — Evidence-ledger foundations

- Logic: ledger ORM models + immutability/append-only triggers; `docs/technical/SCHEMA_OWNERSHIP.md`
- Validation: `pytest services/core/tests/test_ledger_constraints.py -q` → 2 passed

### 3.3 — Hosted Google authentication and self-host OIDC

- Logic: `OidcIssuerAdapter`, activation/bootstrap services, `/api/v1/auth/*` routes, OpenAPI regeneration
- Validation: `pytest services/core/tests/test_auth_oidc.py -q` → 6 passed

### 3.4 — RLS and authorization adversarial suite

- Logic: factories + `runtime_tenant_scope` under `memdot_core` role; security tests; `scripts/check_rls_registry.sh`
- Validation: `pytest tests/security/test_rls_adversarial.py -q` → 4 passed

## 5. Changed-file inventory (grouped)

- **Core DB/auth**: `services/core/src/memdot_core/db/**`, `services/core/src/memdot_core/auth/**`, `services/core/alembic/**`, `services/core/alembic.ini`
- **Domain**: `packages/domain-python/src/memdot_domain/{tenancy,ids}.py`
- **Tests**: `services/core/tests/*`, `tests/security/*`, `tests/support/postgres_fixtures.py`
- **Tooling/CI**: `Makefile`, `.github/workflows/ci.yml`, `scripts/{migrate_domain,check_rls_registry}.sh`, `infra/compose/scripts/migration_job.sh`
- **Contracts**: `packages/contracts/generated/openapi/*` (auth routes)
- **Docs**: `docs/technical/SCHEMA_OWNERSHIP.md`, `CONTEXT.md`, `IMPLEMENTATION_TRACKER.md`

## 6. Data and compatibility impact

- Migration head: `20260716_0001`
- RLS: FORCE RLS + first-party + external-read (non-private) policies on all account-owned tables
- OpenAPI: `/api/v1/auth/oidc/callback`, `/attestation`, `/logout`, `/session`
- Backward compatibility: Phase 2 migration placeholder replaced by explicit Alembic command (no auto-migrate on startup)

## 7. Validation evidence

| Command | Exit |
|---|---|
| `make format-check` | 0 |
| `make lint` | 0 |
| `make typecheck` | 0 |
| `make test` | 0 (100 passed) |
| `make contracts` | 0 |
| `make docs-validate` | 0 |
| `make check` | 0 |
| `make check-rls` | 0 |
| `bash scripts/secret_scan.sh` | 0 |
| `git diff --check` | 0 |

Phase 3 targeted: `pytest services/core/tests tests/security -q` → 37 passed

## 8. Phase 3 exit gate (tracker)

| Gate | Status |
|---|---|
| Migrations clean + repeatable | PASS |
| PostgreSQL enforceable authorization join point | PASS |
| Hosted Google + self-host OIDC + 18+ + sessions | PASS (API layer; Keycloak fixtures in tests) |
| FORCE RLS + adversarial suite | PASS |
| Immutable/append-only structural enforcement | PASS |
| Auth claims separate from product authorization | PASS |

## 9. Security and privacy

- FORCE RLS on 34 account-owned tables; runtime role cannot DDL
- Private Spaces excluded from `external_read` policies
- Session secrets stored hashed only; OIDC validation fail-closed
- No secrets in logs/tests

## 10. Diff evidence

- Patch: `docs/execution/PHASE_03_CANDIDATE.patch`
- Stat: `docs/execution/PHASE_03_CANDIDATE.stat.txt`
- Untracked listing: `docs/execution/PHASE_03_UNTRACKED.txt`

## 11. Known limitations

- Downgrade migration intentionally not automated (owner-controlled)
- Full `make selfhost-smoke` not re-run in this session after migration seam change
- External MCP grant flows complete in Phase 9; schema foundations only
- Compose runtime role passwords for `memdot_core` require operator wiring in production Compose secrets

## 12. Authority confirmation

- No commit, push, merge, deploy, or production mutation performed
- Phase 4 not started

## 13. Requested Codex action

Audit complete Phase 3 candidate at base `2c96aa7` and return PASS, FAIL — CORRECTIONS REQUIRED, or BLOCKED — OWNER DECISION REQUIRED.
