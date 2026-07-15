# Memdot Technical Requirements Document

| Field | Value |
|---|---|
| Status | Implementation baseline for v1 |
| Version | 1.0 |
| Product | Memdot general memory platform with Learning Mode |
| Audience | Engineers, security reviewers, operators, and coding agents |
| Normative language | MUST, MUST NOT, SHOULD, and MAY are requirements terms |

## 1. Purpose and reading order

This document turns the product and functional requirements into testable technical contracts. Memdot is an evidence-preserving memory system, not a chat transcript database and not a thin vector-search wrapper. PostgreSQL and object storage preserve what the user supplied and how it changed; retrieval providers produce rebuildable indexes; the Context Compiler decides what evidence a particular request may receive.

Read this document after the [PRD](../product/PRD.md) and relevant [ADRs](../adr/). Use the [System Architecture](SYSTEM_ARCHITECTURE.md) for diagrams, the [FSD](../product/FSD.md) for visible behavior, the [threat model](SECURITY_PRIVACY_THREAT_MODEL.md) for adversarial cases, and the [release gates](EVALUATION_RELEASE_GATES.md) for promotion criteria.

### 1.1 Requirement and traceability conventions

- `TRD-<DOMAIN>-NNN` identifies a stable technical requirement. Renumbering is forbidden after implementation begins; superseded requirements remain as tombstones.
- `PRD-*` and `FSD-*` links name the product intent and visible flow served by a technical requirement.
- A component is not complete until its linked functional acceptance scenarios and technical tests pass.
- Where a product requirement spans multiple rows, the traceability matrix is authoritative; implementation tickets may refine but must not weaken it.

Domains: `SYS` system boundaries, `DATA` canonical data, `DOC` rich documents, `ING` ingestion, `RET` retrieval/context, `LRN` learning, `NOT` Notion, `MCP` MCP, `API` REST, `SEC` security/privacy, `DEP` deployment, and `OPS` operations.

## 2. System contract

### 2.1 Technology baseline

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-SYS-001 | The browser application MUST be a TypeScript Next.js PWA. Server components MAY render non-sensitive shells, but user memory MUST be loaded through authenticated account-scoped APIs. | PRD-PLAT-001, PRD-PLAT-002; FSD-NAV-*, FSD-OFF-* |
| TRD-SYS-002 | The core domain API MUST be Python FastAPI with SQLAlchemy and Alembic. Only this service owns canonical domain writes. | PRD-CORE-001; FSD-LIB-*, FSD-SPC-*, FSD-DOC-* |
| TRD-SYS-003 | A thin TypeScript MCP edge MUST implement MCP transport and OpenAI-compatible tool envelopes; it MUST call the core API and MUST NOT query databases or Tex directly. | PRD-INT-001, PRD-INT-003; FSD-INT-* |
| TRD-SYS-004 | Python workers, orchestrated by self-hostable Hatchet workflows, MUST own parsing, projection, sync, export, deletion, and long-running model work. HTTP handlers MUST enqueue durable work rather than hold a request open. | PRD-OPS-001, PRD-OPS-002; FSD-ING-*, FSD-EXP-*, FSD-ERR-* |
| TRD-SYS-005 | PostgreSQL MUST be the canonical evidence ledger and authorization join point. Object storage MUST be canonical for immutable binary artifacts. | PRD-CORE-003, PRD-CORE-005; FSD-SRC-*, FSD-DOC-* |
| TRD-SYS-006 | Tex and the local semantic index MUST implement a common retrieval-provider interface. Neither provider may own public IDs, access control, source revisions, citations, deletion truth, or learner evidence. | PRD-CORE-004, PRD-AI-004; FSD-ASK-*, FSD-SRC-* |
| TRD-SYS-007 | Hosted identity MUST use Google as the only user login broker for v1. The application contract MUST remain OIDC-compatible so a self-hosted operator can configure an OIDC issuer and bootstrap the first operator. | PRD-PRIV-001, PRD-PLAT-005; FSD-AUTH-*, FSD-ONB-* |
| TRD-SYS-008 | Model access MUST use Memdot-owned adapters over pinned official provider SDKs or an operator-configured OpenAI-compatible endpoint. A generic credential-bearing model proxy is not trusted infrastructure. | PRD-AI-005, PRD-PLAT-005; FSD-ASK-*, FSD-INT-* |
| TRD-SYS-009 | All inter-service contracts MUST be versioned JSON or Protobuf payloads generated from a single contract package. Breaking changes require a new major contract version and a migration window. | PRD-PLAT-006; FSD-ERR-* |
| TRD-SYS-010 | Account, space, revision, event, and request ownership MUST remain correct when Tex, a model provider, Notion, telemetry, or background workers are unavailable. | PRD-BETA-004, PRD-OPS-002; FSD-ERR-*, FSD-ING-* |

### 2.2 Intended service boundaries

| Component | Owns | Must not own |
|---|---|---|
| Web PWA | Presentation, local pinned cache, optimistic UI, accessibility | Authorization truth, answer keys, model credentials |
| Core API | Domain rules, authorization, canonical writes, receipts, public REST | Binary parsing, long model calls, provider-specific Tex logic |
| MCP edge | Streamable HTTP transport, OAuth challenge, MCP schemas | Canonical storage, retrieval, implicit chat access |
| Workflow workers | Durable jobs and provider adapters | User-session authorization decisions without a signed job scope |
| PostgreSQL | Canonical metadata, immutable revisions/events, RLS, outbox | Original binary bodies |
| Object storage | Immutable originals and parser artifacts | Search truth or access policy |
| Tex adapter | Tex projection and candidate retrieval | Canonical IDs, ACL decisions, irreplaceable facts |
| OSS retrieval adapter | Embedding/rerank/index projection and candidates | Canonical source text or ACL decisions |
| Keycloak/OIDC issuer | Authentication, OAuth clients/tokens | Product permissions or private-space policy |
| Model adapters | Bounded generation/grading/embedding calls | Direct database access or silent persistence |

Dependency direction is `edge/UI -> core application -> domain -> provider ports`; adapters depend inward on ports. Provider code MUST NOT be imported into domain modules.

## 3. Canonical data and provenance

### 3.1 Identity, tenancy, and authorization

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-DATA-001 | Every domain row MUST use a UUIDv7 primary key unless it is a deterministic artifact defined below. User-visible IDs MUST be opaque and MUST NOT encode account or provider identifiers. | PRD-CORE-001, PRD-PRIV-002; FSD-SPC-*, FSD-SRC-* |
| TRD-DATA-002 | `account`, `account_member`, `space`, and `space_member` MUST define tenancy. V1 creates one personal account and owner membership per user, but the schema MUST not assume a single member. | PRD-CORE-001; FSD-ONB-*, FSD-SPC-* |
| TRD-DATA-003 | Every account-owned row MUST carry `account_id`; every space-owned row MUST also carry `space_id`. Foreign keys MUST include or validate the parent account to prevent cross-account attachment. | PRD-PRIV-002; FSD-SPC-*, FSD-ERR-* |
| TRD-DATA-004 | PostgreSQL MUST enable and `FORCE ROW LEVEL SECURITY` on account-owned tables. Each transaction MUST set signed `app.account_id`, `app.actor_id`, and `app.purpose`; pooled connections MUST reset them. Runtime roles MUST not have `BYPASSRLS`. | PRD-PRIV-002; FSD-AUTH-*, FSD-INT-* |
| TRD-DATA-005 | A private space is identified by immutable visibility class `private`. External OAuth/MCP principals MUST be denied before retrieval, and private records MUST be removed again after candidate rejoin. No external scope can override this rule. | PRD-INT-002, PRD-PRIV-002; FSD-SPC-*, FSD-INT-* |
| TRD-DATA-006 | Worker jobs MUST contain an immutable authorization snapshot: account, actor/system purpose, eligible spaces, source revision, and originating request. Workers process one account per transaction. | PRD-OPS-001, PRD-PRIV-002; FSD-ING-*, FSD-ERR-* |

See PostgreSQL's authoritative [row security documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html).

### 3.2 Source and document ledger

The minimum canonical schema is grouped by owner. Names are logical contracts; migrations may add columns but cannot transfer ownership without an ADR.

| Owner | Tables / aggregates | Required invariants |
|---|---|---|
| Identity | `account`, `account_member`, `space`, `space_member`, `external_identity` | OIDC subject is unique per issuer; private visibility is server-enforced |
| Sources | `source`, `source_revision`, `source_blob`, `source_sync_cursor` | A source is logical; revisions are immutable; current revision is an atomic pointer |
| Parsing | `ingestion_job`, `parse_run`, `document_element`, `element_asset`, `chunk` | Parser output is versioned; promoted runs are immutable; no successful page may disappear |
| Authored docs | `authored_document`, `document_revision`, `document_block_index`, `document_patch_proposal` | Revisions immutable; block IDs stable; one current revision pointer |
| Memory | `memory_item`, `memory_revision`, `memory_proposal`, `episode`, `entity`, `relation`, `conflict_set` | Provenance and truth class mandatory; proposals are not canonical |
| Conversations | `conversation`, `conversation_turn`, `interaction_capture` | Completeness and origin recorded; external capture never inferred as complete |
| Learning | `course`, `curriculum_node`, `curriculum_edge`, `assessment_item`, `assessment_revision`, `attempt`, `learner_event`, `review_item`, `learner_projection` | Answer revisions sealed; events append-only; projections rebuildable |
| Retrieval | `projection`, `context_receipt`, `context_receipt_item` | Provider IDs map to canonical revisions; receipts immutable |
| Reliability | `outbox_event`, `workflow_job`, `idempotency_record`, `deletion_request`, `deletion_tombstone`, `audit_event` | Outbox commit is atomic; tombstones survive restore |

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-DATA-007 | `source_revision` MUST store source ID, snapshot SHA-256, captured time, source-native version, MIME type, language hints, byte/page counts, and immutable object key. | PRD-CORE-002, PRD-CORE-003; FSD-ING-*, FSD-SRC-* |
| TRD-DATA-008 | `revision_id = UUIDv5(source_id, snapshot_sha256)`. Reimporting identical bytes/connector snapshots MUST return the existing revision and MAY create a new sync observation, not duplicate content. | PRD-CORE-005, PRD-OPS-001; FSD-ING-* |
| TRD-DATA-009 | Every canonical claim, relationship, derived memory, test item, and answer citation MUST use provenance compatible with W3C PROV concepts: generating activity, agent, entity revision, locator, timestamp, and transformation version. | PRD-CORE-003, PRD-AI-001; FSD-SRC-*, FSD-ASK-* |
| TRD-DATA-010 | Truth class MUST be one of `source_assertion`, `user_assertion`, `external_knowledge`, `derived_proposal`, `approved_derived`, `learner_evidence`, or `system_metadata`. UI and APIs MUST preserve the class; rank or model confidence cannot change it. | PRD-AI-001, PRD-AI-002, PRD-AI-003; FSD-ASK-*, FSD-MEM-* |
| TRD-DATA-011 | Conflicting assertions MUST coexist. `conflict_set` links claims and records `unresolved`, `user_resolved`, or `source_superseded`; resolution never erases history. | PRD-CORE-005, PRD-CORE-006; FSD-SRC-*, FSD-ASK-* |
| TRD-DATA-012 | Mutable pointers such as `current_revision_id` MUST change in the same transaction as an outbox event. Consumers MUST be idempotent and deduplicate by event ID and payload hash. | PRD-OPS-001, PRD-OPS-004; FSD-ING-*, FSD-ERR-* |
| TRD-DATA-013 | Original files, exact Notion JSON, parser raw output, page renders, and extracted assets MUST be retained as immutable objects while the source exists. Derived cache keys MUST include revision and transformation version. | PRD-CORE-003, PRD-PRIV-003; FSD-SRC-*, FSD-EXP-* |
| TRD-DATA-014 | User content MUST remain until user-directed source, course, conversation, space, or account deletion. Operational caches MAY expire; expiration MUST NOT remove the sole copy of user content or evidence. | PRD-PRIV-003, PRD-PRIV-004; FSD-EXP-* |

Provenance semantics follow [W3C PROV-O](https://www.w3.org/TR/prov-o/); the relational schema remains Memdot-owned.

## 4. `MemdotDocument v1`

`MemdotDocument v1` is the portable, parser-independent rich-document contract. Tiptap is an editor implementation, not the persistence format owner. The normative JSON Schema will live in the future contracts package and be published under a stable HTTPS schema URL.

### 4.1 Envelope and nodes

```json
{
  "$schema": "https://schemas.memdot.app/document/v1.json",
  "schema": "memdot-document",
  "schemaVersion": 1,
  "documentId": "019...",
  "root": {
    "type": "doc",
    "content": []
  }
}
```

- Every top-level and nested block node MUST have `attrs.blockId` as UUIDv7. Inline text/marks do not need IDs.
- V1 block nodes: paragraph, heading 1–6, bullet/ordered/task list and item, blockquote, callout, code block, horizontal rule, table/row/cell/header, image, file, embed, math block, citation block, and read-only unsupported block.
- V1 inline nodes/marks: text, hard break, inline math, citation reference, link, bold, italic, underline, strike, code, highlight, subscript, and superscript.
- Links and embeds MUST use an allowlist and normalized HTTPS URLs. Raw HTML, JavaScript URLs, event attributes, arbitrary iframe attributes, and inline executable scripts are forbidden.
- Unknown future nodes MUST be preserved as `unsupported_block` with inert JSON and a visible warning; they MUST not be silently dropped.

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-DOC-001 | The server MUST validate the entire document envelope, node allowlist, depth, asset references, URL policy, unique block IDs, and maximum decoded size before accepting a revision. | PRD-CORE-002; FSD-DOC-*, FSD-ERR-* |
| TRD-DOC-002 | Saving MUST send `baseRevisionId`, a complete validated document, and an idempotency key. The server creates an immutable revision and atomically advances the current pointer only when the base matches. | PRD-CORE-002, PRD-CORE-006; FSD-DOC-* |
| TRD-DOC-003 | A stale base MUST return HTTP `409` with current revision metadata and a block-level diff token. The client offers reload, copy-as-new, or explicit merge; silent last-write-wins is forbidden. | PRD-CORE-006; FSD-DOC-*, FSD-ERR-* |
| TRD-DOC-004 | AI edits MUST be stored as `document_patch_proposal` against one immutable base revision. Operations are `insert_after`, `replace_block`, `delete_block`, `move_block`, and `set_attrs`, addressed by block ID. | PRD-AI-003; FSD-DOC-*, FSD-MEM-* |
| TRD-DOC-005 | Proposal preview MUST apply server-side in an isolated copy. Acceptance creates a normal revision attributed to the user and proposal; a stale proposal becomes conflicted and requires rebase/review. | PRD-AI-003, PRD-CORE-003; FSD-DOC-*, FSD-MEM-* |
| TRD-DOC-006 | Each revision MUST store schema version, normalized JSON SHA-256, author/origin, base revision, proposal ID if any, created time, and a searchable plain-text rendition. | PRD-CORE-003, PRD-CORE-005; FSD-DOC-*, FSD-SRC-* |
| TRD-DOC-007 | Migrations MUST be pure, versioned, idempotent transformations that retain the original revision and fixtures. A client may read older versions but writes only the current schema. | PRD-PLAT-006, PRD-OPS-004; FSD-DOC-* |
| TRD-DOC-008 | Tiptap packages used in core OSS features MUST be permissively licensed. Persistence and round-trip behavior follow Tiptap's documented JSON model while the Memdot schema remains authoritative. | PRD-PLAT-005; FSD-DOC-* |

Reference: [Tiptap persistence](https://tiptap.dev/docs/editor/core-concepts/persistence).

## 5. Ingestion and normalization

### 5.1 Accepted inputs and workflow

V1 accepts PDF and common image formats, DOCX, PPTX, Markdown, TXT, direct paste, authored Memdot documents, captured conversations, and selected Notion pages. Arbitrary URL crawling, audio/video, spreadsheets, and Google Drive are not v1 ingestion contracts.

```text
snapshot -> verify -> parse -> normalize -> validate -> promote
         -> structural chunk -> map/proposal generation -> project -> ready
```

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-ING-001 | `POST /ingestions` MUST create an idempotent ingestion intent and presigned upload when needed. Completion MUST verify declared byte size, SHA-256, MIME sniffing, malware result, and ownership before enqueueing. | PRD-CORE-001, PRD-OPS-001; FSD-ING-* |
| TRD-ING-002 | Baseline safeguards are 100 MiB per object, 1,000 pages per source, two active parse workflows per account, and a bounded account queue. Limits are deployment configuration, not monthly product quotas; queued work MUST remain durable. | PRD-BETA-002, PRD-BETA-003; FSD-ING-*, FSD-ERR-* |
| TRD-ING-003 | Original objects MUST be quarantined until validation. Archives, active content, malformed container relationships, password-protected documents, and decompression bombs MUST fail safely with a user-actionable code. | PRD-PRIV-002, PRD-OPS-002; FSD-ING-*, FSD-ERR-* |
| TRD-ING-004 | Docling MUST be the baseline parser for born-digital PDF, ordinary scans, DOCX, and PPTX. Native adapters MUST parse Markdown, text, Memdot documents, conversations, and Notion blocks without flattening source structure first. | PRD-CORE-002; FSD-ING-*, FSD-NOT-* |
| TRD-ING-005 | Low-confidence scans, difficult layout/tables/formulas, Hindi/code-mixed OCR, and handwriting MAY route to the gated PaddleOCR-VL/PP-Structure profile. Handwriting output MUST be visibly experimental. | PRD-PLAT-003; FSD-ING-*, FSD-ERR-* |
| TRD-ING-006 | A parse profile hash MUST cover parser name/version, model weights, configuration, normalizer version, and element-schema version. `parse_run_id = UUIDv5(revision_id, profile_hash)`. | PRD-CORE-005, PRD-OPS-004; FSD-ING-* |
| TRD-ING-007 | A parser-neutral `document_element` MUST store element ID/type/order, exact text, retrieval-normalized text, language, parent/previous/next IDs, heading path, assets, confidence, warnings, and provenance locator. | PRD-CORE-003; FSD-SRC-*, FSD-ING-* |
| TRD-ING-008 | Element locators MUST preserve page and bounding polygon for paged inputs, character/line span for text, native path for office files, block ID for Memdot/Notion, and table cell/formula coordinates where applicable. | PRD-CORE-003, PRD-AI-001; FSD-SRC-*, FSD-ASK-* |
| TRD-ING-009 | `element_id = UUIDv5(parse_run_id, canonical_locator + content_hash)`. `chunk_id = UUIDv5(parse_run_id, ordered_element_ids + boundaries + chunk_profile)`. | PRD-CORE-005, PRD-OPS-004; FSD-ING-* |
| TRD-ING-010 | Exact parser text and normalized retrieval text MUST be separate. Normalization may repair whitespace and Unicode presentation but MUST NOT silently translate, paraphrase, or alter formulas, code, identifiers, or numbers. | PRD-AI-001, PRD-PLAT-003; FSD-SRC-* |
| TRD-ING-011 | Promotion MUST be atomic and only after structural validation: every input page accounted for, locators valid, IDs unique, parent graph valid, and low-confidence/unsupported content surfaced. A failed run leaves the prior promoted run active. | PRD-OPS-002, PRD-BETA-004; FSD-ING-*, FSD-ERR-* |
| TRD-ING-012 | Parser upgrades MUST produce a shadow run, compare it with the active run using the evaluation corpus, and switch the source pointer atomically. Old runs remain addressable until source history is purged. | PRD-CORE-005, PRD-OPS-004; FSD-SRC-*, FSD-ING-* |

Primary parser references: [Docling](https://github.com/docling-project/docling), [Docling document model](https://docling-project.github.io/docling/concepts/docling_document/), [Docling confidence](https://docling-project.github.io/docling/concepts/confidence_scores/), and [PaddleOCR-VL](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html).

### 5.2 Structural chunks

- Chunks MUST follow headings, list/table boundaries, slides, source blocks, and semantic paragraphs before size targets.
- Initial target is 350–700 model tokens with at most 100 tokens of structural overlap; tables, code, formulas, and assessment items remain atomic even when larger.
- Each chunk stores an ordered set of element IDs, heading path, exact citation span, normalized text, language, and chunk-profile version.
- Contextual headers used for embedding are derived fields and MUST NOT be presented as source quotations.
- Changing chunk or embedding profiles creates new projections; it never mutates source elements.

## 6. Retrieval and the Context Compiler

### 6.1 Candidate lanes

| Lane | Canonical implementation | Purpose |
|---|---|---|
| Exact | PostgreSQL full-text, `pg_trgm`, identifiers, metadata | Names, codes, quoted phrases, formulas, filenames |
| Temporal/version | PostgreSQL revisions and timestamps | “What changed?”, historical and current-edition queries |
| Graph | PostgreSQL relations and recursive traversal | Course hierarchy, prerequisites, entities, provenance |
| OSS semantic | pgvector-compatible local provider plus embedding/rerank adapters | Always-available dense candidates and self-host parity |
| Tex | Tex provider adapter | Hosted semantic, episodic, entity, and temporal candidates after gates pass |

PostgreSQL search behavior follows its [full-text search](https://www.postgresql.org/docs/current/textsearch.html) and JSONB contracts; vector behavior follows [pgvector](https://github.com/pgvector/pgvector).

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-RET-001 | Every retrieval request MUST first resolve an immutable eligibility set from actor, purpose, account, permitted spaces, private-space rule, current/historical mode, and deletions. | PRD-CORE-004, PRD-INT-001, PRD-INT-002; FSD-ASK-*, FSD-INT-* |
| TRD-RET-002 | The query planner MUST classify one or more intents: `exact`, `semantic`, `temporal`, `graph`, `episodic`, `synthesis`, and `learning`. Classification is advisory and MUST preserve exact search. | PRD-CORE-004, PRD-LEARN-002; FSD-ASK-* |
| TRD-RET-003 | Each enabled lane returns at most 50 candidate projection IDs. Provider results MUST be joined through `projection` to current canonical revisions and filtered again by RLS, space eligibility, deletion, and source status. | PRD-PRIV-002, PRD-CORE-005; FSD-ASK-*, FSD-INT-* |
| TRD-RET-004 | Candidate fusion MUST use deterministic weighted reciprocal-rank fusion with initial `k=60`: temporal direct/quoted exact 2.0, exact 1.5, OSS semantic 1.0, Tex 1.0, graph 0.8. Weights are versioned configuration and may change only through benchmark evidence. | PRD-CORE-004, PRD-OPS-004; FSD-ASK-* |
| TRD-RET-005 | Exact quoted, identifier, formula, and user-pinned hits MUST be retained in the rerank set. The semantic reranker evaluates up to 80 fused candidates and returns at most 30 before structural expansion. | PRD-CORE-004, PRD-AI-001; FSD-ASK-* |
| TRD-RET-006 | Structural expansion occurs after ranking and may add headings, parent blocks, adjacent elements, table headers, provenance, and confirmed prerequisites. Suggested/unconfirmed graph edges cannot block or silently change learning context. | PRD-LEARN-001, PRD-AI-004; FSD-ASK-*, FSD-TST-* |
| TRD-RET-007 | Current queries MUST prefer the current source revision. Historical/change queries MUST return explicit revision timestamps and must not merge conflicting editions as if simultaneous. | PRD-CORE-005, PRD-CORE-006; FSD-SRC-*, FSD-ASK-* |
| TRD-RET-008 | Conflicts among eligible claims MUST be returned as conflicts with each citation. The compiler MUST NOT select a winner based solely on retrieval or model score. | PRD-CORE-006, PRD-AI-001; FSD-ASK-*, FSD-SRC-* |
| TRD-RET-009 | Context packing MUST honor the caller's hard token/character budget. Default allocation is 70% cited evidence, 15% conflict/temporal context, 10% citation metadata, and 5% headroom; unused portions may be reassigned to evidence. | PRD-AI-004; FSD-ASK-*, FSD-INT-* |
| TRD-RET-010 | When required evidence does not fit, the compiler MUST record omitted candidate IDs/reasons and return `partial=true`; it MUST not truncate text so that its citation locator becomes false. | PRD-AI-004, PRD-BETA-004; FSD-ASK-*, FSD-ERR-* |
| TRD-RET-011 | Every compilation MUST create an immutable context receipt containing query hash, actor/client, purpose, policy version, eligible spaces, provider/profile versions, candidate ranks, selected canonical revision IDs and locators, conflicts, omissions, budget, and context hash. | PRD-AI-004, PRD-PRIV-006; FSD-ASK-*, FSD-INT-* |
| TRD-RET-012 | Context receipts MUST be content-minimized: they reference canonical content rather than copy full passages. A separate content-free route receipt stores provider, model, processing region, data categories, token counts, and policy version. | PRD-PRIV-005, PRD-PRIV-006; FSD-INT-*, FSD-EXP-* |
| TRD-RET-013 | Native Ask may generate a source-first answer from compiled evidence. Any unsupported model/world knowledge MUST appear in a separately labeled `External knowledge` section and MUST NOT be indexed as source truth without proposal approval. | PRD-AI-001, PRD-AI-002, PRD-AI-003; FSD-ASK-*, FSD-MEM-* |
| TRD-RET-014 | Retrieval and answer caches MUST key on account, eligibility hash, query hash, source-revision set, compiler version, model/profile, and privacy purpose. Cache entries MUST be invalidated by deletion tombstones and permission changes. | PRD-PRIV-002, PRD-OPS-004; FSD-ASK-*, FSD-INT-* |

### 6.2 Tex contract and OSS fallback

Tex's public guidance states that it is not the authoritative audit store; Memdot therefore treats it as a derived provider. See [Tex migration guidance](https://github.com/metacoglabs/docs/blob/852c4cf105df58e488a1e9e8a877e3a4524dd113/migration/from-redis.mdx#L78-L83).

The provider port is logically:

```text
upsert(batch, tenant_context, idempotency_key) -> provider_ids/status
retrieve(query, tenant_context, filters, limit) -> candidates
delete(provider_ids, tenant_context, idempotency_key) -> status
job_status(provider_job_id) -> status
health() -> capabilities/status
```

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-RET-015 | `projection` MUST map canonical source revision/chunk or memory revision to provider, surface/profile version, provider document/memory ID, provider job ID, payload hash, status, indexed time, error, and tombstone time. | PRD-CORE-003, PRD-OPS-001; FSD-ING-*, FSD-SRC-* |
| TRD-RET-016 | Tex MUST remain disabled for production traffic until contract tests prove stable external IDs/idempotency, account isolation/filtering, metadata behavior, citation mapping, retry/job semantics, physical deletion behavior, latency, outage response, and export/rebuild capability. | PRD-PRIV-002, PRD-OPS-004; FSD-INT-*, FSD-ERR-* |
| TRD-RET-017 | The OSS lane MUST index every eligible canonical revision even when Tex is healthy. On Tex timeout, circuit-open, or invalid response, retrieval continues with exact/graph/temporal/OSS lanes, marks the receipt degraded, and never broadens eligibility. | PRD-PLAT-005, PRD-BETA-004, PRD-OPS-004; FSD-ASK-*, FSD-ERR-* |
| TRD-RET-018 | Tex responses with unknown, cross-account, stale, deleted, or unmapped IDs MUST be discarded and counted as security/integrity signals. Repeated isolation failures automatically disable the provider globally. | PRD-PRIV-002, PRD-OPS-003; FSD-ERR-* |
| TRD-RET-019 | Projection rebuild MUST scan canonical revisions by monotonic cursor, emit idempotent upserts, validate counts/hashes, shadow-query the new surface, and atomically switch the active projection profile. | PRD-OPS-001, PRD-OPS-004; FSD-ING-*, FSD-ERR-* |

The initial OSS dense index uses exact pgvector search. HNSW is enabled only after corpus measurements justify its recall/latency/memory trade-off. Embedding and reranker models are deployment configuration selected by the release benchmark and license review; canonical data never embeds a model-specific vector column without a profile/version key.

## 7. Learning Mode

### 7.1 Curriculum and assessment

- Curriculum entities are `course`, `unit`, `objective`, `concept`, `source_unit`, and `assessment_item`.
- Relations are `part_of`, `prerequisite`, `related`, `assesses`, and `supported_by`.
- Confirmed `prerequisite` edges MUST form a directed acyclic graph. AI suggestions are visibly unconfirmed and cannot block Test or Review.
- The model is CASE-shaped for future interoperability but Memdot does not claim CASE conformance until import/export tests exist. Reference: [1EdTech CASE](https://standards.1edtech.org/case/).

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-LRN-001 | Assessment revisions MUST be immutable and store type, prompt, sealed answer/rubric, rationale, source revision locators, target concept, difficulty, guessing chance, creator/model/prompt profile, and verification state. | PRD-LEARN-001, PRD-LEARN-003; FSD-TST-*, FSD-SRC-* |
| TRD-LRN-002 | Item state is `draft`, `provisional`, `human_verified`, or `retired`. Retirement prevents new attempts but preserves historical attempts. Answer/rubric fields MUST never appear in pre-submission APIs, MCP context, client logs, or telemetry. | PRD-LEARN-003, PRD-PRIV-002; FSD-TST-*, FSD-INT-* |
| TRD-LRN-003 | V1 test types are MCQ, short answer, and written explain/apply. Grading records deterministic rule, human decision, or model/profile and confidence; low-confidence model grades remain provisional and cannot establish demonstration. | PRD-LEARN-003, PRD-LEARN-004; FSD-TST-* |
| TRD-LRN-004 | `learner_event` is append-only and includes event ID, account/user/course, concept/item/revision, attempt, client event ID, event type, occurred/received time, payload schema version, and provenance. Corrections are compensating events. | PRD-LEARN-004, PRD-OPS-004; FSD-TST-*, FSD-REV-* |
| TRD-LRN-005 | Event types include attempt started, response captured, confidence recorded, hint requested/revealed, answer revealed, grade recorded, review rated, item retired, user chat marker, and projection corrected. | PRD-LEARN-004, PRD-LEARN-006; FSD-TST-*, FSD-REV-* |
| TRD-LRN-006 | Eligible demonstrated evidence requires one primary concept, immutable source/item revision, response captured before feedback, no revealed answer, no substantive hint, eligible grade, and explicit assessment event. MCQ alone may support but cannot solely prove delayed demonstration. | PRD-LEARN-004, PRD-LEARN-007; FSD-TST-*, FSD-ASK-* |
| TRD-LRN-007 | Evidence projection states are `unassessed`, `practicing`, `demonstrated`, and `delayed_demonstrated`; recall states are `current`, `due`, and `lapsed`; confidence is preserved separately as `guessing`, `unsure`, or `sure`. | PRD-LEARN-004, PRD-LEARN-005, PRD-LEARN-006; FSD-TOD-*, FSD-REV-* |
| TRD-LRN-008 | User-marked conversations may create practice, confusion, insight, or candidate evidence events. They may affect priority, but post-feedback content cannot establish demonstrated/delayed recall; a pre-feedback captured response may be promoted only when all eligibility rules pass. | PRD-INT-004, PRD-LEARN-004; FSD-ASK-*, FSD-MEM-* |
| TRD-LRN-009 | FSRS schedules review items, not global concept mastery. Initial desired retention is 0.90. Rating mapping is Again for incorrect/skipped/revealed/substantively hinted, Hard for correct with scaffold/minor error, Good for unhinted correct, and Easy only for explicitly effortless correct recall. | PRD-LEARN-005; FSD-REV-* |
| TRD-LRN-010 | Scheduling priority is deterministic: lapsed/due prerequisites, overdue items, new items with confirmed prerequisites, then user-pinned work. The event ledger MUST replay to identical projections and schedules. | PRD-LEARN-005, PRD-OPS-004; FSD-TOD-*, FSD-REV-* |

FSRS integration follows the open [FSRS implementation/reference](https://github.com/open-spaced-repetition/ts-fsrs), with Memdot-owned event semantics. BKT or opaque “mastery AI” is not in v1.

## 8. Notion synchronization

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-NOT-001 | The connector MUST use Notion OAuth, least privileges, encrypted tokens, recursive paginated block reads, rate-limit handling, and an exact raw JSON snapshot before normalization. | PRD-INT-005, PRD-PRIV-002; FSD-NOT-*, FSD-INT-* |
| TRD-NOT-002 | Users select inbound pages. Only content beneath one explicitly selected Memdot root page/database is writable by Memdot; selected source pages outside that root are read-only. | PRD-INT-005; FSD-NOT-* |
| TRD-NOT-003 | The source-native page/block ID, last-edited time, hierarchy, annotations, unsupported block JSON, and asset references MUST be preserved. Expiring assets MUST be copied to canonical object storage while authorized. | PRD-CORE-003, PRD-INT-005; FSD-NOT-*, FSD-SRC-* |
| TRD-NOT-004 | A webhook is only a change signal. Workers MUST refetch the selected subtree, compare source-native versions/hashes, and periodically reconcile to recover missed or reordered signals. | PRD-OPS-001, PRD-OPS-004; FSD-NOT-*, FSD-ERR-* |
| TRD-NOT-005 | Memdot write-back MUST use stable Notion mapping rows and idempotency hashes. It writes approved Memdot documents/proposals only beneath the dedicated root and MUST not rewrite unsupported source blocks. | PRD-AI-003, PRD-INT-005; FSD-NOT-*, FSD-MEM-* |
| TRD-NOT-006 | If both sides changed since the shared base, sync MUST create a conflict with base, Notion, and Memdot versions. It MUST pause that item until the user chooses Notion, Memdot, or a reviewed merge. | PRD-CORE-006; FSD-NOT-*, FSD-ERR-* |
| TRD-NOT-007 | Notion deletion outside the Memdot root creates a source-deletion proposal; it does not immediately erase Memdot history. Deleting inside the Memdot root follows user-confirmed sync policy and tombstones mappings. | PRD-PRIV-003, PRD-INT-005; FSD-NOT-*, FSD-EXP-* |
| TRD-NOT-008 | Disconnect MUST revoke/delete stored connector credentials and stop future sync while retaining imported user content until the user separately deletes it. | PRD-PRIV-003; FSD-NOT-*, FSD-INT-* |

Live authorized-workspace contract tests are a release gate; undocumented Notion behavior must not be invented.

## 9. MCP public contract

### 9.1 Transport and authorization

The remote server is mounted at `POST /mcp` using MCP Streamable HTTP. It advertises OAuth protected-resource metadata, uses Authorization Code + PKCE, validates issuer/audience/expiry/scopes on every request, and supports immediate grant revocation. SSE compatibility MAY be added as a bridge; stdio is available only in an optional local self-host adapter.

The read grant is `memdot.memory.read` over the account's complete eligible non-private memory. Separate write grants are `memdot.memory.propose` and `memdot.interaction.record`. V1 exposes no external delete or `memory.commit` grant; conversation deletion remains an authenticated first-party REST action. The consent screen explicitly names whole-account access, private-space exclusion, chats/attempts eligibility, client identity, and downstream-provider risk.

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-MCP-001 | `search` MUST accept exactly `{ "query": string }`; no caller-supplied account, space, or private flag is allowed. Query is trimmed Unicode, 1–2,048 characters. | PRD-INT-001, PRD-INT-003; FSD-INT-* |
| TRD-MCP-002 | `search` MUST return `{ "results": [{ "id", "title", "url" }] }`, at most 20 entries. `id` is stable and opaque; `title` is safe display text; `url` is an absolute HTTPS URL the authenticated user can open in Memdot. | PRD-INT-003, PRD-AI-004; FSD-INT-*, FSD-SRC-* |
| TRD-MCP-003 | `fetch` MUST accept exactly `{ "id": string }` and return `{ "id", "title", "text", "url", "metadata"? }`. `text` includes immutable revision/citation labels; metadata may include source type, revision time, locators, truth class, and conflict state. | PRD-INT-003, PRD-CORE-003; FSD-INT-*, FSD-SRC-* |
| TRD-MCP-004 | MCP tool responses MUST place the object in `structuredContent` and the same JSON serialized in a text content block. Search/fetch URLs MUST never be empty, bearer-token URLs, or non-openable internal object keys. | PRD-INT-003; FSD-INT-* |
| TRD-MCP-005 | The citation URL MUST resolve through the web application, require the user's current session, reauthorize the item, and show revision, locator, provenance, and deletion/unavailable state. The opaque URL alone conveys no access. | PRD-PRIV-002, PRD-AI-004; FSD-SRC-*, FSD-INT-* |
| TRD-MCP-006 | `prepare_context` accepts query, purpose `general|learning`, optional historical timestamp, and hard budget. Like every MCP read, it searches the complete eligible non-private account; v1 exposes no caller-controlled Space narrowing or expansion. It returns evidence blocks, citations, conflicts, omissions, `partial/degraded`, and receipt ID. | PRD-AI-004, PRD-LEARN-002; FSD-ASK-*, FSD-INT-* |
| TRD-MCP-007 | `propose_memory` accepts an idempotency key, proposed text/structure, truth class, optional target non-private space, source receipt/citations, and client origin. It returns proposal ID/status; it never mutates canonical memory. | PRD-AI-003, PRD-INT-003; FSD-MEM-*, FSD-INT-* |
| TRD-MCP-008 | `record_interaction` accepts idempotency key, a required non-private target Space ID, client conversation ID, role, content, occurred time, optional reply linkage/context receipt, and completeness `single_turn|partial_thread|complete_import`. It appends a captured turn and never changes learner evidence automatically. | PRD-INT-004, PRD-LEARN-004; FSD-INT-*, FSD-MEM-* |
| TRD-MCP-009 | MCP cannot passively inspect a host conversation. The UI and docs MUST state that external capture is limited to explicit tool calls/imports and preserve completeness status. | PRD-INT-004; FSD-INT-* |
| TRD-MCP-010 | `search`, `fetch`, and `prepare_context` MUST be annotated read-only. Proposal/capture tools MUST be annotated as writes and require their exact scopes. Tool names and schemas are versioned compatibility surfaces. | PRD-INT-003, PRD-PRIV-002; FSD-INT-* |
| TRD-MCP-011 | Tool failures MUST use safe MCP errors with stable machine codes and correlation ID. Authorization, private-space existence, raw provider IDs, source contents, and stack traces MUST not leak in errors. | PRD-PRIV-002, PRD-OPS-002; FSD-ERR-* |
| TRD-MCP-012 | Revoking a grant MUST invalidate new calls immediately and refresh tokens within one minute. Previously returned data cannot be clawed back; consent and revocation UI must state this. | PRD-PRIV-002, PRD-PRIV-004; FSD-INT-* |

Compatibility references: [OpenAI MCP company-knowledge contract](https://developers.openai.com/apps-sdk/build/mcp-server#company-knowledge-compatibility) and the [MCP architecture/isolation model](https://modelcontextprotocol.io/specification/2025-06-18/architecture).

## 10. REST API contract

All routes are under `/api/v1`. JSON uses camelCase at the public boundary and typed internal DTOs. Errors use `application/problem+json` with `type`, `title`, `status`, stable `code`, safe `detail`, `instance`, and `correlationId`. Validation errors add field pointers.

### 10.1 Routes

| Method and route | Purpose | Idempotency / authorization |
|---|---|---|
| `POST /ingestions` | Create upload/connector ingestion intent | `Idempotency-Key`; account write |
| `POST /ingestions/{id}/complete` | Verify upload and enqueue | `Idempotency-Key`; owner account |
| `GET /ingestions/{id}` | Job stages, warnings, failure, retryability | Owner account |
| `POST /search` | Rich native search with filters/history | Account read; private allowed only for first-party user session |
| `GET /items/{id}` | Fetch canonical item/revision/citation | Reauthorize every request |
| `POST /context` | Compile context and receipt | Purpose-scoped account read |
| `POST /memory-proposals` | Create proposal | `Idempotency-Key`; proposal write |
| `POST /memory-proposals/{id}/decision` | Approve/edit/reject | `Idempotency-Key`; first-party user only |
| `POST /interactions` | Capture an external/native turn | `Idempotency-Key`; interaction write |
| `GET /conversations` | Paginated conversation list | Account read |
| `GET /conversations/{id}/turns` | Cursor-paginated turns | Account read |
| `DELETE /conversations/{id}` | Durable deletion workflow | `Idempotency-Key`; owner only |
| `POST /exports` | Account/space export | `Idempotency-Key`; recent re-authentication |
| `POST /deletions` | Source/space/account deletion | `Idempotency-Key`; recent re-authentication |

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-API-001 | Bearer API/OAuth requests MUST validate issuer, audience, expiry, subject, scopes, and revocation. Browser mutation requests also require same-site session and CSRF protection. | PRD-PRIV-002; FSD-AUTH-*, FSD-INT-* |
| TRD-API-002 | All successful writes MUST echo request ID and canonical resource/version. Reusing an idempotency key with the same fingerprint returns the original result; a different fingerprint returns `409 idempotency_conflict`. | PRD-OPS-001; FSD-ERR-* |
| TRD-API-003 | Collections MUST use opaque signed cursor pagination with a deterministic `(sort_value,id)` order. Offset pagination is forbidden for mutable event/source lists. | PRD-CORE-005; FSD-LIB-*, FSD-MEM-* |
| TRD-API-004 | API DTOs MUST distinguish `missing`, `redacted`, `deleted`, `processing`, `failed`, `partial`, and `degraded`; clients must not infer these from null. | PRD-BETA-004, PRD-OPS-002; FSD-ERR-*, FSD-ING-* |
| TRD-API-005 | Long work returns `202` with job ID and polling URL. Job stages are monotonic except explicit retry; retry creates an attempt record under the same logical job. | PRD-OPS-001, PRD-OPS-002; FSD-ING-*, FSD-EXP-* |
| TRD-API-006 | Upload bodies MUST use presigned object URLs. The API never buffers 100 MiB files; completion verifies object generation, hash, ownership, and expiry. | PRD-OPS-001, PRD-PRIV-002; FSD-ING-* |
| TRD-API-007 | Search/context request limits, concurrency, and safety backpressure MUST return `429` with `Retry-After` or `202` queued status. They MUST never silently drop accepted work. | PRD-BETA-002, PRD-BETA-003, PRD-BETA-004; FSD-ERR-* |
| TRD-API-008 | Public contracts MUST be generated from OpenAPI, tested for backward compatibility, and carry deprecation/sunset headers for at least one supported release before removal. | PRD-PLAT-006; FSD-ERR-* |

## 11. Security, privacy, and lifecycle

The detailed adversary analysis lives in the threat model; these are implementation invariants.

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-SEC-001 | Hosted signup MUST require successful Google authentication and explicit 18+ self-attestation before account creation. Under-18 selection is rejected without collecting identity documents. | PRD-PRIV-001; FSD-AUTH-*, FSD-ONB-* |
| TRD-SEC-002 | Source text is untrusted data. Parsers run isolated without ambient network/credentials; retrieved instructions cannot invoke tools, alter policies, select scopes, or become system prompts. | PRD-PRIV-002, PRD-AI-001; FSD-ING-*, FSD-ASK-* |
| TRD-SEC-003 | Hosted canonical data and default managed inference MUST remain in GCP Mumbai (`asia-south1`). Delhi (`asia-south2`) stores encrypted disaster-recovery backups. Non-regional BYOK providers require explicit disclosure/consent. | PRD-AI-005, PRD-PRIV-002; FSD-INT-*, FSD-SET-* |
| TRD-SEC-004 | Managed AI MUST use bounded stateless requests, disabled provider storage/logging where supported, no provider file/session stores, and no search grounding unless separately approved. BYOK changes credential/payment, not provider geography or retention. | PRD-AI-005, PRD-PRIV-002; FSD-ASK-*, FSD-INT-* |
| TRD-SEC-005 | Secrets MUST be envelope-encrypted: Cloud KMS/Secret Manager hosted and OpenBao Transit self-hosted. Plaintext connector/model keys exist only in process memory for a bounded call and are never logged. | PRD-PRIV-002, PRD-PLAT-005; FSD-INT-* |
| TRD-SEC-006 | Telemetry MUST use a strict allowlist. Prompts, responses, search queries, filenames/titles, source text, attempt text, authorization headers, cookies, and credentials are forbidden in logs/traces/analytics. | PRD-PRIV-005, PRD-OPS-003; FSD-INT-*, FSD-ERR-* |
| TRD-SEC-007 | Essential availability/security telemetry is enabled hosted. Product analytics is separate opt-in and off by default; session replay and research-content donation are not v1 defaults. OSS telemetry is off by default. | PRD-PRIV-005, PRD-PLAT-005; FSD-SET-* |
| TRD-SEC-008 | Deletion MUST immediately revoke sessions, grants, integrations, and keys in scope; purge live PostgreSQL/object/Tex/derived data within seven days; expire encrypted backups within 35 days; and replay tombstones after restore. | PRD-PRIV-003, PRD-PRIV-004; FSD-EXP-*, FSD-INT-* |
| TRD-SEC-009 | `deletion_tombstone` MUST contain only irreversible identity hash, resource class, deletion time, and purge checkpoints. It MUST prevent reimport/reprojection after restore without retaining deleted content. | PRD-PRIV-003, PRD-OPS-004; FSD-EXP-* |
| TRD-SEC-010 | Export MUST include originals, current/history metadata, authored documents, approved memories, conversations, course graph, learner events, citations, and a machine-readable manifest with hashes. Provider-internal embeddings/IDs are excluded as rebuildable implementation data. | PRD-PRIV-004, PRD-PLAT-006; FSD-EXP-* |
| TRD-SEC-011 | Content-free pseudonymous security/access audit events MAY be retained for one year, segregated from product content. Final retention/erasure interaction requires prelaunch Indian legal review. | PRD-PRIV-003, PRD-PRIV-005; FSD-EXP-* |
| TRD-SEC-012 | Offline content MUST be explicitly pinned, encrypted in an account-partitioned IndexedDB store with a non-extractable per-device key, and erased on logout/account switch. The UI must not represent this as protection from a compromised origin/browser. | PRD-PLAT-002, PRD-PRIV-002; FSD-OFF-* |
| TRD-SEC-013 | Account export/deletion, connector changes, BYOK changes, and MCP grants MUST require recent authentication. Administrative access requires MFA, just-in-time authorization, reason, and content-free audit. | PRD-PRIV-002, PRD-PRIV-004; FSD-SET-*, FSD-EXP-* |
| TRD-SEC-014 | Offline v1 MUST be limited to explicitly pinned reading and a seven-day review pack. Packs exclude sealed answers/rubrics; offline responses are provisional and create canonical grading, learner events, Evidence Twin changes, and FSRS updates only after idempotent online acknowledgement. | PRD-PLAT-002, PRD-LEARN-005; FSD-OFF-*, FSD-REV-* |

India child-data obligations are described by [DPDP Act Section 9](https://www.indiacode.nic.in/show-data?abv=CEN&actid=AC_CEN_45_0_00003_2023-22_1763464807080&orderno=9&orgactid=AC_CEN_45_0_00003_2023-22_1763464807080&sectionId=101275&sectionno=9&statehandle=123456789%2F1362). This specification is a product/security baseline, not legal advice.

## 12. Deployment and OSS parity

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-DEP-001 | Hosted v1 MUST deploy stateless web/API/MCP and workers in Mumbai on a regional GKE deployment, with Cloud SQL for PostgreSQL HA, private GCS, regional Artifact Registry/log buckets, and Cloud KMS/Secret Manager. | PRD-PLAT-005, PRD-OPS-004; FSD-ERR-* |
| TRD-DEP-002 | Delhi MUST hold encrypted 35-day disaster-recovery backups. PostgreSQL PITR target is seven days; beta targets are RPO <=15 minutes and RTO <=4 hours, verified quarterly. | PRD-OPS-004; FSD-ERR-*, FSD-EXP-* |
| TRD-DEP-003 | Organization policy MUST restrict content-bearing hosted resources to India locations; regional model endpoints are mandatory. Content-free DNS, certificate, and edge control metadata are documented separately. | PRD-PRIV-002; FSD-SET-* |
| TRD-DEP-004 | The complete self-host profile MUST run with Docker Compose and include Caddy, web, API, MCP, workers, Hatchet, PostgreSQL+pgvector, SeaweedFS, Keycloak, OpenBao, and OpenTelemetry/Grafana components. | PRD-PLAT-005; FSD-INT-*, FSD-ERR-* |
| TRD-DEP-005 | Self-hosted core functionality MUST operate with Tex disabled and with local embedding/reranking plus either an operator-configured local OpenAI-compatible model endpoint or direct provider credentials. | PRD-PLAT-005, PRD-AI-005; FSD-ASK-*, FSD-TST-* |
| TRD-DEP-006 | Provider selection MUST be configuration through stable ports; hosted-only conditionals in domain behavior are forbidden. Migrations and exported documents/events are identical across hosted/self-hosted deployments. | PRD-PLAT-005, PRD-PLAT-006; FSD-EXP-* |
| TRD-DEP-007 | Images and dependencies MUST be pinned by digest/version, SBOM-generated, vulnerability-scanned, signed, and built reproducibly. Model weights require license, hash, provenance, and evaluation records. | PRD-PLAT-005, PRD-OPS-004; FSD-ERR-* |
| TRD-DEP-008 | Deployment changes use expand/migrate/contract sequencing. Database migrations run as a separate bounded job; application startup MUST NOT auto-run destructive migrations. | PRD-OPS-004; FSD-ERR-* |

Official location references: [Cloud SQL regions](https://docs.cloud.google.com/sql/docs/postgres/region-availability-overview), [Cloud Storage locations](https://docs.cloud.google.com/storage/docs/locations), and [resource location constraints](https://docs.cloud.google.com/organization-policy/restrict-locations).

## 13. Reliability, performance, and observability

### 13.1 SLOs and budgets

| ID | Budget / SLO | Measurement |
|---|---|---|
| TRD-OPS-001 | MCP `search` p95 <=1.5 s | Server duration, warm service, excluding client network |
| TRD-OPS-002 | MCP `fetch` p95 <=500 ms | Server duration for existing text item |
| TRD-OPS-003 | Context compilation p95 <=3 s | Excludes answer-model generation; includes retrieval/rerank |
| TRD-OPS-004 | API accepted-write response p95 <=750 ms | Long work returns durable `202` |
| TRD-OPS-005 | Hosted beta monthly availability >=99.5% | Web/API/MCP usable; planned maintenance disclosed |
| TRD-OPS-006 | Zero unauthorized/private candidate output | Continuous security invariant, not an error budget |
| TRD-OPS-007 | 100-page born-digital document ready p95 <=10 min; OCR p95 <=20 min | Queue wait reported separately; corpus profile recorded |
| TRD-OPS-008 | Projection lag p95 <=5 min and deletion revoke <=1 min | Per provider and account |

These are launch gates, not promises to ignore overload. The system may queue parsing, shed optional reranking/model work, or use OSS fallback; it may not lose accepted work or broaden data access.

### 13.2 Durable work and failure behavior

| ID | Requirement | Product / functional links |
|---|---|---|
| TRD-OPS-009 | Every workflow step MUST declare timeout, bounded exponential retry with jitter, idempotency key, retryable codes, and compensation/terminal behavior. Poison jobs enter a visible dead-letter state. | PRD-OPS-001, PRD-OPS-002; FSD-ING-*, FSD-ERR-* |
| TRD-OPS-010 | Circuit breakers isolate Tex, model, Notion, OCR, and object-store failures. A provider outage MUST not exhaust request threads or database connections. | PRD-BETA-004, PRD-OPS-002; FSD-ERR-* |
| TRD-OPS-011 | OpenTelemetry MUST propagate correlation, trace, account pseudonym, workflow, receipt, and provider/profile IDs across services while enforcing the content denylist. | PRD-OPS-003, PRD-PRIV-005; FSD-ERR-* |
| TRD-OPS-012 | Metrics MUST cover request/job latency and errors, queue age/depth, projection lag, candidate rejection reasons, context partial/degraded rate, citation validity, provider circuit state, deletion checkpoints, and token/cost totals without content. | PRD-OPS-003, PRD-OPS-004; FSD-ERR-* |
| TRD-OPS-013 | Alerts MUST page on cross-account/private candidate detection, deletion resurrection, unavailable canonical storage, authentication bypass indicators, and sustained SLO burn. Provider degradation creates an operator alert and user-visible status, not a security bypass. | PRD-PRIV-002, PRD-OPS-003; FSD-ERR-* |

### 13.3 Failure-mode contract

| Failure | Required server behavior | Visible state / recovery |
|---|---|---|
| Duplicate upload/callback | Return original idempotent result | One source/revision; no duplicate billing/work |
| Parser crash/timeout | Preserve original and prior promoted run; bounded retry | Failed/partial with diagnostics and reprocess |
| Low OCR confidence | Route gated fallback or promote with warnings | Visible page/element warnings; never “fully ready” silently |
| Tex unavailable | Open circuit; exact/graph/temporal/OSS retrieval | `degraded=true`, receipt names omitted lane |
| Local embedding unavailable | Exact/graph/temporal and Tex if valid | Degraded state; queue projection repair |
| Reranker unavailable | Use versioned fused ordering | Degraded receipt; no eligibility change |
| Model unavailable | Return cited evidence/context; do not invent answer | Retry/provider choice; sources remain usable |
| Notion rate limit | Persist cursor and retry after provider delay | Sync delayed with last successful time |
| Notion conflict | Pause only mapped item | Three-way review UI |
| Stale document save | Reject with 409 | Reload/copy/explicit merge |
| Revoked MCP token | Reject before tool dispatch | Reconnect consent flow |
| Deletion during job | Tombstone wins; worker aborts and purges artifacts | Deletion progress; never reproject |
| Queue overload | Durable queue/backpressure; reject only before acceptance | Queued status or 429 with retry time |
| Object/database outage | Stop promotion and canonical writes | Read-only/degraded status; recovery from canonical backup |

## 14. Verification and release criteria

Implementation is not complete until the linked [Evaluation and Release Gates](EVALUATION_RELEASE_GATES.md) pass. At minimum:

- Schema/RLS tests attempt cross-account attachment and retrieval for every account-owned table.
- Property tests prove deterministic revision/parse/element/chunk IDs and idempotent event replay.
- Golden documents cover English, Hindi, Hinglish, multi-column scans, tables, formulas, slides, malformed files, and experimental handwriting.
- Retrieval tests measure exact, temporal, graph, semantic, conflict, citation, historical, outage, and deletion behavior.
- Contract tests validate MCP shapes in ChatGPT-compatible clients and authorized openable URLs; Claude remote MCP and Gemini CLI are interoperability targets.
- Learning tests prove no answer-revealed, substantively hinted, low-confidence graded, or post-feedback response becomes demonstrated evidence.
- Notion tests use a real authorized test workspace for pagination, unsupported blocks, assets, missed webhooks, rate limits, conflicts, deletion, and disconnect.
- Security tests perform at least 10,000 adversarial cross-account/private-space calls with zero leakage.
- Docker self-host tests run the full acceptance suite with Tex disabled and telemetry off.
- Restore drills replay deletion tombstones and prove deleted data cannot reappear.

## 15. Traceability summary

| Product capability | Product IDs | Functional IDs | Technical owners |
|---|---|---|---|
| Spaces, library, sources, rich documents | PRD-CORE-001..006 | FSD-LIB-*, FSD-SPC-*, FSD-DOC-*, FSD-SRC-* | TRD-SYS, TRD-DATA, TRD-DOC |
| Ingestion and processing | PRD-CORE-002..005, PRD-OPS-001..004 | FSD-ING-*, FSD-ERR-* | TRD-ING, TRD-OPS |
| Search, provenance, history, conflicts | PRD-CORE-003..006, PRD-AI-001..004 | FSD-ASK-*, FSD-SRC-* | TRD-DATA, TRD-RET |
| Learning Map, Ask, Test, Review | PRD-LEARN-001..007 | FSD-TOD-*, FSD-ASK-*, FSD-TST-*, FSD-REV-* | TRD-LRN, TRD-RET |
| MCP and external capture | PRD-INT-001..004 | FSD-INT-*, FSD-MEM-* | TRD-MCP, TRD-API, TRD-SEC |
| Notion synchronization | PRD-INT-005 | FSD-NOT-* | TRD-NOT, TRD-ING |
| Privacy, consent, export, deletion | PRD-PRIV-001..006 | FSD-AUTH-*, FSD-ONB-*, FSD-INT-*, FSD-EXP-* | TRD-DATA, TRD-SEC |
| PWA, offline, language, accessibility | PRD-PLAT-001..006 | FSD-OFF-*, FSD-A11Y-* | TRD-SYS, TRD-SEC, TRD-DEP |
| Free beta safety and integrity | PRD-BETA-001..004 | FSD-ERR-*, FSD-ING-* | TRD-API, TRD-OPS |
| OSS and hosted operations | PRD-PLAT-005..006, PRD-OPS-001..004 | FSD-EXP-*, FSD-ERR-* | TRD-DEP, TRD-OPS |

## 16. Explicit integration gates and non-goals

- Tex production promotion is blocked until the contract gates in TRD-RET-016 pass. Private Tex implementation behavior is not inferred from public repositories.
- Exact embedding/reranker/model versions are blocked on license and frozen-corpus evaluation; adapters and profile fields are fixed now.
- Notion two-way sync is blocked on live authorized-workspace tests.
- Payment/billing, institutions, minor accounts, real-time collaboration, native mobile apps, browser extension, web crawling, audio/video, Google Drive, Calendar/Tasks, and high-stakes exam proctoring are not v1 technical contracts.
- “Full OSS parity” means every product workflow has a self-hosted provider path; it does not mean hosted operational services or third-party models are bundled.
