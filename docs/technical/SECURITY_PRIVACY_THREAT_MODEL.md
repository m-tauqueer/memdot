# Security, Privacy, and Threat Model

Status: **Founding specification**
Date: **2026-07-15**
This is product and engineering guidance, not legal advice.

## 1. Purpose and security posture

Memdot holds original educational material, personal notes, retained
conversations, assessment attempts, and derived learner evidence. Whole-account
AI access makes a compromised grant materially more damaging than a normal
single-document integration. Security therefore uses explicit trust boundaries,
canonical re-authorization on every read, minimal external disclosure, durable
deletion, and visible context receipts.

Hard rule: no quality, availability, or beta-growth objective can override
account isolation, private-space exclusion, sealed answer keys, deletion, or
credential protection.

## 2. Assets and data classes

| Class | Examples | Default handling |
|---|---|---|
| C0 public | Static app shell, public docs | Public caching allowed |
| C1 account metadata | Profile, space names, settings | Encrypted transport/storage; no public logs |
| C2 user content | Sources, notes, chats, attempts, course graph | Account-isolated; retained until deletion |
| C3 sensitive learning | Raw answers, confidence, misconceptions, learner events | Same isolation as C2; sealed from inappropriate contexts |
| C4 credentials | OAuth tokens, model keys, connector secrets | Envelope encrypted; decrypt only in owning service |
| C5 security metadata | Grant, access, deletion, incident events | Content-free, pseudonymous, segregated |

Memdot's hosted design is not end-to-end encrypted: authorised server-side
services must parse, index, search, and compile content. The product must say so
plainly rather than implying that encryption at rest prevents server processing.

## 3. Trust boundaries

- Browser/PWA to Memdot edge.
- MCP host to Memdot MCP resource server.
- Web and MCP edges to the Core API.
- Core API to PostgreSQL and object storage.
- Workflow workers to untrusted uploaded files and connector content.
- Retrieval orchestrator to Tex and local semantic providers.
- Model router to managed/BYOK inference providers.
- Hosted control plane to self-hosted installations.

Uploaded documents, Notion blocks, retrieved text, rich-document embeds, model
output, and MCP tool arguments are untrusted input even when they originate from
the account owner.

## 4. Identity, sessions, and authorization

### SEC-AUTH-001 — Hosted identity

Hosted v1 supports Google authentication only. The server owns an opaque,
HttpOnly, Secure, SameSite session cookie and CSRF protection. OAuth/OIDC tokens
are not exposed to browser JavaScript.

### SEC-AUTH-002 — Adult boundary

First login requires an explicit 18+ confirmation before content may be stored.
An under-18 response ends onboarding without collecting additional identity
evidence. India defines a child as a person under 18 and imposes additional
obligations for processing children's data; v1 does not attempt that product.
[DPDP Act, Section 9](https://www.indiacode.nic.in/show-data?abv=CEN&actid=AC_CEN_45_0_00003_2023-22_1763464807080&orderno=9&orgactid=AC_CEN_45_0_00003_2023-22_1763464807080&sectionId=101275&sectionno=9&statehandle=123456789%2F1362)

### SEC-AUTH-003 — Tenant enforcement

The Core API performs explicit account/space authorization. PostgreSQL adds
`FORCE ROW LEVEL SECURITY` under a transaction-scoped account context. Runtime
roles cannot bypass RLS; migration ownership uses a separate role. Provider IDs
never serve as authorization evidence.

### SEC-AUTH-004 — External AI grant

`memdot.memory.read` means all eligible memory types across all non-private
spaces. The consent screen lists sources, approved memories, completed attempts,
learner summaries, and captured chats; it warns that a downstream AI provider's
retention policy applies after disclosure. Private status cannot be overridden
by any v1 scope.

Access tokens are short-lived and audience-bound to the Memdot MCP/API resource.
Refresh tokens rotate. Revocation invalidates both before the next successful
read. Writes use separate `source.write`, `proposal.write`,
`interaction.write`, and `interaction.delete` grants. V1 exposes no external
canonical `memory.commit` grant.

## 5. Primary threats and controls

| Threat | Required controls | Release rule |
|---|---|---|
| Cross-account retrieval | App auth, RLS, canonical post-filter, canary tests | Any leak blocks release |
| Private-space disclosure | Deny before candidate retrieval and after provider return | Any disclosure blocks release |
| Provider-ID enumeration | Opaque IDs; indistinguishable `NOT_FOUND`; auth on fetch | 100% adversarial pass |
| Prompt injection in sources | Treat content as evidence, never instructions; fixed system/tool policy | No permission/policy change |
| Stale/deleted Tex result | Canonical revision/deletion rejoin before response | Zero visible stale tombstones |
| Answer-key exposure | Server-side sealed keys; purpose-specific projections | Zero pre-submission keys |
| Malicious upload/parser exploit | Byte-level MIME check, malware scan, isolated no-network worker, CPU/RAM/time/page bounds | No privileged parser execution |
| Rich-content XSS | Strict block allowlist, HTML sanitisation, CSP, no active SVG/HTML, sandboxed allowlisted embeds | XSS corpus pass |
| Credential theft | Envelope encryption, service-specific policies, no workflow payload keys, no logs | Secret scanning and access audit pass |
| OAuth confused deputy | PKCE, issuer/JWKS/audience/resource checks, redirect allowlist | Protocol suite pass |
| Duplicate/out-of-order jobs | Transactional outbox, idempotency keys, deterministic IDs | Replay converges exactly |
| Deletion resurrection | Tombstone workflow, projection purge, deletion ledger replay after restore | Restore drill pass |
| Unlimited-beta cost abuse | Request/body limits, concurrency queues, abuse detection, global budget circuit breakers | Graceful queue/degrade; no data loss |

## 6. Retrieval and model-provider controls

1. Calculate the authorised account/space/revision set before retrieval.
2. Send only bounded candidate material and non-sensitive routing metadata to a
   provider.
3. Rejoin every provider candidate to canonical PostgreSQL state.
4. Filter deleted, historical-by-default, wrong-edition, unauthorised, private,
   sealed, and pending-proposal records.
5. Produce a user-visible context receipt and a separate content-free route audit.

Tex and local vector stores are derived indexes, not security boundaries. A Tex
failure or delayed deletion cannot make data visible because canonical filtering
is mandatory.

The hosted managed default uses paid regional inference in India where the
selected service contract permits it. BYOK changes the credential and payer, not
the external provider's geography, logging, or retention. Every cross-border or
non-zero-retention route requires disclosure before enablement. Model adapters
decrypt only the selected credential just in time and never persist prompts in
provider-specific session/file features by default.

## 7. Conversation and learner privacy

- Native conversations are canonical account content.
- External conversations enter only through `record_interaction` or an import;
  capture completeness is always visible.
- A captured conversation does not update learning evidence automatically.
- A user may later mark a response as candidate practice/confusion/insight.
- Post-feedback, answer-revealed, or substantively hinted responses cannot prove
  demonstrated or delayed-demonstrated recall.
- Learner misconceptions remain learner evidence and never become source truth.

## 8. Hosted region, logging, and research use

- Canonical hosted data, regional logs, primary backups, and managed inference
  remain in the selected India region unless a user enables a disclosed external
  provider.
- Mumbai is primary; encrypted Delhi backups provide disaster recovery.
- Operational telemetry uses a strict allowlist: request ID, timing, error code,
  component/provider/model, token count, cost, queue age, and policy version.
- Do not log prompts, responses, search queries, filenames, source titles, raw
  attempts, credentials, cookies, tokens, or authorization headers.
- Product analytics is opt-in and off by default. There is no session replay.
- Real user content may enter research/evaluation only through a separate,
  explicit donation consent and de-identification workflow.
- Self-hosted telemetry is off by default; the operator owns its deployment's
  residency and processor choices.

## 9. Retention, export, and deletion

User sources, document revisions, approved memories, conversations, attempts,
and learning evidence remain until the user deletes the relevant object, course,
space, conversation, or account. Temporary failed-upload/parser artefacts expire
after seven days; successful transient parser artefacts expire after 30 days
unless required for reproducibility. Unapproved proposals expire after 30 days.

Deletion sequence:

1. Hide the object and revoke affected sessions/grants immediately.
2. Commit a durable tombstone and deletion-outbox event.
3. Purge live PostgreSQL payloads, object blobs, search rows, Tex/local
   projections, offline sync eligibility, and connector mappings within seven
   days.
4. Retain only legally/security-required content-free audit evidence.
5. Let encrypted backups expire within 35 days.
6. Replay the deletion ledger after every restore before serving reads.

Target beta recovery: RPO at most 15 minutes and RTO at most four hours. Run a
quarterly restore plus deletion-replay exercise.

## 10. PWA and rich-content controls

Cache Storage contains only versioned public app assets. Authenticated pinned
documents/assets and seven-day review packs use a per-account IndexedDB namespace
encrypted with a non-extractable WebCrypto key. Logout, account switch, deletion,
or unpin removes data and keys. Tokens never enter Cache Storage or IndexedDB.

Offline attempts are provisional append-only events. Server replay deduplicates
them and recomputes authoritative evidence/FSRS state. V1 does not offer offline
editing, Ask, import, integration sync, MCP, or new test generation.

Rich documents accept only the `MemdotDocument v1` allowlist. Links allow
`http`, `https`, and `mailto`; embeds are provider-allowlisted, click-to-load,
sandboxed, and rendered without arbitrary HTML. KaTeX uses `trust:false`; code
blocks are never executable.

## 11. Incident response

- Severity 0: confirmed/suspected cross-account or private-space leak,
  credential exposure, deleted-data resurrection, or learner-state corruption.
- Immediately disable the affected route/provider, preserve content-free
  forensic evidence, rotate credentials, assess scope, and notify the incident
  owner.
- Maintain an India-specific notification runbook and validate legal timeframes
  before launch.
- Provider compromise must support rapid adapter disablement without disabling
  canonical exact/local retrieval.

## 12. Launch gates

- Threat-model review and processor/subprocessor inventory.
- OAuth/MCP scope, audience, redirect, revocation, and enumeration tests.
- At least 10,000 cross-account/private-space/prompt-injection attack calls with
  zero data exposure.
- Restore/deletion replay and credential-rotation drills.
- Provider-region/no-log configuration verification.
- Dependency lockfiles, SBOM, image scanning, pinned digests, and model-license
  review.
- External legal review of DPDP notices, audit retention, deletion, breach
  workflow, and the adult-only boundary.

## 13. Traceability

Primary drivers: PRD privacy/portability/beta requirements; FSD authentication,
spaces, integrations, export/deletion, offline, and error-state requirements;
ADR-0002, ADR-0003, ADR-0007, ADR-0008, ADR-0010, ADR-0011, and ADR-0013.
