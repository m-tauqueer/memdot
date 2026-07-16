# Phase 3 Codex correction and acceptance report

Date: 2026-07-16
Baseline: `2c96aa7`
Verdict: **PASS**
Next phase: **not authorized**

## Corrections completed

- Replaced forgeable raw tenant GUC trust with Core-signed, 60-second tenant
  context envelopes covering account, actor, purpose, issued time, and nonce.
- Revoked default PUBLIC execution on privileged `SECURITY DEFINER` functions
  and removed direct runtime DML on OIDC state/replay and current-pointer tables.
- Replaced the pointer mutation flag API with atomic source/document
  pointer-plus-outbox functions, including event-ID/hash idempotency checks.
- Changed browser authentication from browser-submitted ID tokens to a
  server-side OIDC authorization-code exchange with PKCE S256, encrypted
  short-lived verifier storage, hashed state/nonce, and durable replay checks.
- Applied the configured session pepper to session, CSRF, state, and nonce
  hashes instead of unsalted SHA-256.
- Replaced the nominal RLS table loop with a connected fixture that seeds a
  real row in every account-owned table. The 34-table matrix now tests known-ID
  read/update/delete isolation; pointer writes are separately tested through
  their sole atomic function seam.
- Added live negative controls for missing FORCE RLS, forbidden runtime grants,
  and leaked PUBLIC function execution.
- Updated Compose secret materialization, Keycloak client configuration, CI,
  schema ownership, configuration inventory, context, tracker, and AI map.

## Validation evidence

- `make lint`: PASS.
- `make typecheck`: PASS (TypeScript and Pyright, zero errors).
- Focused auth, migration, schema-drift, role, ledger, negative-control, and RLS
  suite: PASS. The final complete Python suite passed 159 tests; TypeScript
  workspace suites also passed.
- Prior Phase 3 `make selfhost-smoke`: accepted from Grok correction round 1.
  It was deliberately not repeated because these corrections are covered by
  fast database/auth gates and the owner requested relief from repeated
  30-minute infrastructure runs.
- Final format, contracts, docs, whitespace, secret, and diff gates are recorded
  in the accepting commit handoff.

## Remaining boundary

The production Google IdP live end-to-end remains an environment release gate;
the adapter boundary and server-side code/PKCE flow are covered with an injected
issuer/token endpoint. Phase 4 API and workflow behavior has not started.
