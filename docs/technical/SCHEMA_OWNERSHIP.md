# Schema ownership inventory (Phase 3)

| Table | Owner | Mutability | Notes |
|---|---|---|---|
| account, user, account_member | Core | mutable | Tenancy root; status check-constrained |
| space, space_member | Core | mutable | Private visibility immutable once set |
| hosted_adult_attestation | Core | append-only | Hosted 18+ gate |
| external_identity, actor | Core | mutable | Identity linkage via auth seam functions |
| browser_session, session_revocation | Core | mutable/revocation | Hashed secrets; safe lookup via `memdot_auth_load_session` |
| external_client_grant | Core | mutable | External OAuth grants |
| operator_bootstrap | Core | append-only | Self-host one-time singleton (`singleton_key=1`) |
| oidc_login_challenge, oidc_token_replay | Core | auth-only | Not account-owned; no runtime table DML; narrow auth functions only |
| memdot_context_secret | migrate | internal | HMAC seal key; no runtime DML grants |
| source, source_revision, source_blob | Core | revision immutable | UUIDv5(source_id, sha256); composite Space FKs |
| authored_document, document_revision | Core | revision immutable | Document ledger |
| parse_run, document_element | Core | revision immutable | Parsing foundation |
| provenance_record, truth_classification | Core | append-only | PROV-compatible metadata; truth-class checks |
| conflict_set, conflict_member | Core | append-only membership | Conflicts preserved |
| proposal | Core | mutable status | Forced `derived_proposal`; not canonical memory |
| conversation, conversation_turn | Core | turn append-only | No learner evidence |
| audit_event | Core | append-only | Content-minimized audit |
| current_source_revision, current_document_revision | Core | mutable pointers | Runtime mutation only through atomic `memdot_set_current_*_revision` functions |
| outbox_event, idempotency_record | Core | append-only / replay | Reliability foundations |
| durable_job, job_attempt | Workers+Core | job mutable, attempts append-only | Signed snapshots in Phase 4 |
| projection_state | Workers | mutable derived | Rebuildable |

## Protected tenant context (TRD-DATA-004)

Runtime code must not unlock rows by calling `set_config` on `app.*` GUCs.
Context is established only through SECURITY DEFINER `memdot_begin_tenant_context`,
which validates actor, membership/grant, purpose, and revocation, then seals the
transaction with a Core-signed, time-bounded HMAC over
`(account_id, actor_id, purpose, issued_at, nonce)`. RLS policies call
`memdot_rls_ok(account_id)`, which re-verifies the signature and expiry. The `memdot_core` runtime
role is `NOBYPASSRLS`, cannot DDL, and cannot assume migrate/admin roles.
`migration` / `admin` purposes are rejected for the runtime role. Identity bootstrap
and session lookup use non-enumerating auth seam functions rather than open
migration GUCs.

Current-revision changes and their outbox event are performed by one database
function in one transaction. Runtime has SELECT but no direct INSERT, UPDATE, or
DELETE privilege on the pointer tables. Reusing an event ID is accepted only
when its payload hash and resulting revision match; conflicting reuse fails.

Derived projections (Tex, pgvector, caches) remain outside this schema per ADR-0002 and ADR-0003.
