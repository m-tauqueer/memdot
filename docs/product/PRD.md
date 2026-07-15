# Memdot Product Requirements Document

**Status:** Approved product contract for v1 implementation
**Audience:** Founder, product/design, engineering, security, operations, and AI coding agents
**Last updated:** 2026-07-15
**Normative language:** **MUST**, **SHOULD**, and **MAY** describe requirement strength. Requirement IDs are permanent; retired requirements remain recorded rather than being reused.

## 1. Founder summary

Memdot is a general personal-memory platform with Learning as its first flagship mode. It gives a person one durable, inspectable memory across their files, authored notes, selected Notion content, Memdot conversations, approved memories, and learning evidence. That memory works inside Memdot and through explicitly authorized AI clients.

The product is not differentiated by “upload a PDF and chat.” Its defensible behavior is the combination of:

1. **Evidence Ledger:** every retained claim, source, version, memory proposal, conversation, and learning event has an owner, provenance, and history.
2. **Context Compiler:** retrieval combines exact, semantic, temporal, graph, and learning context; returns only authorized evidence; and explains what was included, omitted, or in conflict.
3. **Evidence Twin:** source coverage, demonstrated learning, recall state, and learner confidence remain separate instead of collapsing into an opaque mastery score.
4. **Portable Memory:** the same governed memory can be used from Memdot, ChatGPT-compatible MCP clients, Claude, Gemini CLI, and future integrations.

V1 is a public, free, India-first beta for individuals aged 18 or older. Hosted Memdot uses Google sign-in and an explicit age confirmation. The UI is English-first; ingestion, retrieval, and memory support English, Hindi, and Hinglish. The open-source product is licensed under Apache 2.0 and must remain fully useful when self-hosted without Tex.

## 2. Product thesis and positioning

### 2.1 Problem

People scatter knowledge across files, note applications, chats, and AI tools. Existing products typically optimize one part of the problem:

- note applications organize authored pages but do not reliably compile context for multiple AI clients;
- document chat products answer from a temporary collection without durable user-owned memory and learning evidence;
- flashcard products schedule practice but do not preserve the complete source and reasoning trail;
- generic RAG systems retrieve chunks but do not model source versions, curriculum structure, user confidence, or permission-aware context receipts.

The result is repeated setup, untraceable answers, stale context, and learning signals that confuse exposure with understanding.

### 2.2 Product promise

> Memdot remembers what the user owns, where it came from, how it changed, what the learner has actually demonstrated, and what an authorized AI is allowed to see.

### 2.3 Product principles

| Principle | Required product behavior |
|---|---|
| Source before synthesis | Answers and derived memories link back to immutable source revisions and locators. |
| Provenance is visible | Users can distinguish imported source, direct authorship, external knowledge, AI proposal, conversation, and learning evidence. |
| Retrieval is not authority | Search rank never decides truth, access, version currency, or learning mastery. |
| No silent AI writes | AI-generated facts and edits are proposals until the user approves them. |
| Exposure is not learning | Reading, asking, or seeing an answer cannot establish demonstrated recall. |
| Portable but bounded | External AI clients can use eligible account memory, while private spaces are categorically excluded. |
| Reversible systems | Derived indexes can be rebuilt; source versions, decisions, and events remain auditable. |
| Graceful overload | Safety controls may queue or temporarily limit work but may never silently lose or corrupt it. |
| OSS parity | Self-hosting is a complete product path, not a crippled community edition. |

## 3. Audience, personas, and jobs to be done

### 3.1 Launch audience

- **Primary:** university students, adult exam candidates, and independent adult learners in India.
- **Secondary:** professionals and researchers who need trustworthy personal memory without using Learning mode for every space.
- **Future, not v1:** schools, institutions, teams, and users under 18.

The launch does not claim to serve children. India’s Digital Personal Data Protection Act defines additional obligations for children; Memdot therefore requires an 18+ confirmation and reserves minors for a later guardian/institution/legal design. See [DPDP Act, Section 9](https://www.indiacode.nic.in/show-data?abv=CEN&actid=AC_CEN_45_0_00003_2023-22_1763464807080&orderno=9&orgactid=AC_CEN_45_0_00003_2023-22_1763464807080&sectionId=101275&sectionno=9&statehandle=123456789%2F1362). This document is product guidance, not legal advice.

### 3.2 Personas

#### P1 — The course learner

Imports a syllabus, slides, notes, and readings; wants a reliable map, cited explanations, and review that reflects demonstrated recall rather than activity.

**Jobs:**

- “Help me see what this course contains and where my sources cover it.”
- “Answer from my material, show conflicts, and tell me when outside knowledge is used.”
- “Test what I can retrieve without hints and bring it back at the right time.”

#### P2 — The exam candidate

Has a large, multilingual corpus and limited time. Needs exact retrieval for terms and formulas, weak-prerequisite detection, and a defensible review queue.

**Jobs:**

- “Prioritize what is due, weak, and important for my exam.”
- “Keep Hindi/Hinglish material searchable without losing exact terminology.”
- “Let me explain an answer, not just choose an MCQ.”

#### P3 — The memory builder

Uses Notion, Markdown, files, and AI chats. Wants a durable, portable memory with version history and controlled AI access.

**Jobs:**

- “Import without flattening my original structure or losing where a claim came from.”
- “Let my preferred AI use the same memory without exposing private material.”
- “Keep AI suggestions reviewable and let me export or delete everything.”

#### P4 — The self-hosting operator

Runs Memdot for personal use, requires a documented deployment with open components, configurable OIDC, and no mandatory Tex dependency.

**Jobs:**

- “Run the full feature set with local retrieval and my own storage/model choices.”
- “Understand upgrades, backups, deletion, and provider boundaries.”

## 4. Product model

### 4.1 General Memory Core

Every account contains spaces. A space owns sources, documents, conversations, approved memories, proposals, and activity. A normal space supports collecting, authoring, searching, asking, and portable AI access.

A **private space** is a categorical privacy boundary. Its content can be used inside authenticated Memdot surfaces, but never appears in external MCP search, fetch, context preparation, or interaction-derived context. The user cannot weaken that boundary with a per-client toggle in v1.

### 4.2 Learning mode

Learning is a mode applied to a space, adding:

- courses, units, objectives, concepts, prerequisites, and source coverage;
- source-backed questions and sealed answers;
- assessment attempts, confidence, feedback, and misconceptions;
- an evidence state and an independent recall schedule;
- Today, Test, and Review workflows.

Learning follows **Map → Ask → Test → Review**. A stable syllabus tree is the primary navigation. Local graph views may show prerequisites, dependants, sources, and evidence, but v1 does not expose a decorative global “knowledge graph.”

### 4.3 Evidence Twin

Memdot keeps these dimensions separate:

- **Source coverage:** what material supports a concept.
- **Evidence:** `unassessed → practicing → demonstrated → delayed-demonstrated`.
- **Recall:** `current | due | lapsed`.
- **Confidence calibration:** performance grouped by `guessing | unsure | sure`.

Reading, asking, time spent, answer views, or MCQ selection alone do not prove learning. Only an eligible assessment event can update demonstrated evidence. The exact event rules belong to the [FSD](./FSD.md) and [TRD](../technical/TRD.md).

## 5. End-to-end journeys

### J1 — New learner to first review

1. The adult signs in with Google, confirms 18+, and accepts product terms.
2. They create a Learning space and course, then upload a syllabus and class material.
3. Memdot preserves each source revision, parses it, displays processing quality, and proposes a course map.
4. The user confirms or edits suggested concepts and prerequisite relationships.
5. They ask a scoped question and receive a cited answer that labels any external knowledge.
6. They start a test, state confidence before feedback, submit, and review source-backed feedback.
7. Eligible attempt evidence updates; FSRS schedules an item-level review.
8. Today later explains why that item is due.

### J2 — Existing knowledge into portable memory

1. The user imports files and selected Notion pages.
2. Library shows original, current revision, processing status, citations, and any unsupported blocks.
3. The user connects an external AI and grants whole-account access to eligible non-private memory.
4. The AI calls `search`/`fetch` or prepares a bounded context. Memdot records a context receipt.
5. If the AI proposes a memory, it appears in Memory → Proposed; it is not canonical until approved.
6. A private-space item never appears in any external result.

### J3 — Two-way Notion work area

1. The user selects inbound source pages and creates or selects one dedicated Memdot root in Notion.
2. Source pages outside that root sync inward and remain read-only from Memdot.
3. Approved Memdot documents can publish beneath the dedicated root.
4. Concurrent edits create an explicit conflict for review; Memdot never silently overwrites either side.

### J4 — Failure, history, and recovery

1. A large or difficult source is queued, partially processed, or fails.
2. The UI shows what completed, what is unavailable, whether an alternate parser is running, and what the user can do.
3. A retry creates or resumes an idempotent job; it does not create duplicate canonical revisions.
4. The user can inspect older revisions and ask a historical question without confusing old content with current truth.

### J5 — Deletion and portability

1. The user requests an export and receives original sources plus portable canonical data and history.
2. They delete an item, a conversation, a space, or the account.
3. It disappears immediately from product and external retrieval, and deletion progress remains visible until derived stores and backups have honored the documented policy.
4. A rebuild or backup restoration cannot resurrect a tombstoned item.

## 6. V1 product requirements

### 6.1 Memory Core

| ID | Requirement | Priority | Product acceptance |
|---|---|---:|---|
| PRD-CORE-001 | Users MUST be able to create, rename, archive, restore, and delete general or Learning spaces. A space can be private. | P0 | Every retained object has exactly one owning account and at least one owning space; private status is visible wherever access is configured. |
| PRD-CORE-002 | Library MUST accept PDF/images, DOCX, PPTX, Markdown, TXT, paste, rich documents, and selected Notion pages while retaining originals and immutable revisions. | P0 | The user can open the original/current revision and see processing state, version time, and provenance. Handwriting is visibly experimental. |
| PRD-CORE-003 | Memdot MUST provide source-aware search and fetch across eligible memory, including exact terms, dates, revisions, and citations. | P0 | Search results identify item type, space, source/version, snippet, and stable openable URL; deleted or unauthorized material never appears. |
| PRD-CORE-004 | Users MUST be able to author rich documents with stable block identity, revision history, backlinks, citations, code, math, tables, media, and reviewable AI patches. | P0 | Saving never silently overwrites a newer revision; AI changes are inspectable before acceptance. Databases and real-time collaboration are absent. |
| PRD-CORE-005 | Source conflicts and historical versions MUST remain visible rather than being silently merged into one answer. | P0 | Ask and item inspection distinguish current, historical, conflicting, and unresolved evidence. |
| PRD-CORE-006 | Conversations, approved memories, proposals, completed attempts, and their provenance MUST be inspectable in the account memory model. | P0 | Users can distinguish source truth, authored content, external knowledge, AI proposal, conversation, and learning evidence. |

### 6.2 Learning mode

| ID | Requirement | Priority | Product acceptance |
|---|---|---:|---|
| PRD-LEARN-001 | A Learning space MUST support courses, units, objectives, concepts, prerequisites, and source coverage using a syllabus-tree-first interface. | P0 | Suggested nodes/edges are visibly unconfirmed and editable; unconfirmed prerequisites cannot block progression. |
| PRD-LEARN-002 | Ask MUST support explicit account, space, course, source, concept, and historical scope with source-first citations. | P0 | The answer displays scope, citations, conflicts, outside-knowledge labels, and a context receipt. |
| PRD-LEARN-003 | Test MUST support MCQ, short-answer, and written explain/apply items with sealed answers and source/rubric versions. | P0 | A learner cannot receive the sealed answer before submitting or explicitly revealing it. |
| PRD-LEARN-004 | Demonstrated learning MUST be derived only from eligible assessment events and MUST remain separate from exposure, practice, and self-confidence. | P0 | Revealed answers, substantive hints, post-feedback capture, and ungradable responses cannot establish demonstrated recall. |
| PRD-LEARN-005 | Review MUST schedule item-level practice using FSRS and explain why each item is due. | P0 | A user can filter by due state/course/time and inspect the event that changed a schedule. |
| PRD-LEARN-006 | Test MUST collect confidence before feedback and report calibration separately from correctness. | P1 | The user can compare accuracy across guessing, unsure, and sure responses without confidence affecting source truth. |
| PRD-LEARN-007 | The product MUST optimize for source-grounded delayed success on novel items, not chat volume, streaks, or time spent. | P0 | The north-star metric is calculated from eligible delayed assessments and reported separately from engagement. |

### 6.3 AI behavior and truth

| ID | Requirement | Priority | Product acceptance |
|---|---|---:|---|
| PRD-AI-001 | Native answers MUST use the user’s evidence first and cite immutable source/document revisions. | P0 | A factual claim derived from account memory has a working citation or is marked unsupported. |
| PRD-AI-002 | Model knowledge outside eligible account evidence MUST be clearly labeled “External knowledge” and MUST NOT be promoted automatically to source truth. | P0 | Users can visually and programmatically distinguish externally supplied content. |
| PRD-AI-003 | AI-created facts, memories, relationships, and document edits MUST be proposals until explicitly approved. | P0 | Rejecting a proposal changes no canonical source or approved memory. |
| PRD-AI-004 | Every compiled AI context MUST produce a user-inspectable receipt describing scope, evidence, versions, conflicts, omissions, and budget decisions. | P0 | The receipt can reproduce which immutable records were supplied without storing hidden chain-of-thought. |
| PRD-AI-005 | Hosted Memdot MUST provide a managed model default and MAY allow optional BYOK with provider/region/retention disclosure. | P1 | The user knows which provider handles a request; self-hosting can select a supported provider without losing product functionality. |

### 6.4 Integrations and portable access

| ID | Requirement | Priority | Product acceptance |
|---|---|---:|---|
| PRD-INT-001 | An explicitly connected AI client MUST be able to search/fetch the user’s entire eligible non-private account, including relevant retained chats and completed attempts. | P0 | A single grant covers eligible account memory; private-space fixtures return no result under all MCP tools. |
| PRD-INT-002 | V1 MCP MUST expose `search`, `fetch`, `prepare_context`, `propose_memory`, and `record_interaction` with separately enforceable read and write scopes. | P0 | Search/fetch are read-only; neither a proposal nor interaction capture commits source truth or learning evidence. |
| PRD-INT-003 | Native Memdot conversations MUST be captured automatically; external conversations MUST be marked complete, partial, or unavailable based on explicitly supplied turns. | P0 | The UI never claims passive access to a host AI’s full conversation. |
| PRD-INT-004 | Users MUST be able to connect, inspect, and revoke an AI integration, with immediate authorization effect and an activity trail. | P0 | A revoked client’s next request fails and its prior reads remain auditable. |
| PRD-INT-005 | Notion MUST support selected-page inbound sync plus approved Memdot document write-back only beneath a dedicated Memdot root. | P0 | Source pages outside the root cannot be modified by Memdot; conflicts require review. |

### 6.5 Privacy, identity, retention, and control

| ID | Requirement | Priority | Product acceptance |
|---|---|---:|---|
| PRD-PRIV-001 | Hosted v1 MUST use Google sign-in and require an explicit 18+ confirmation before account activation. | P0 | A user who declines or does not confirm cannot enter the product; age confirmation is auditable without collecting date of birth. |
| PRD-PRIV-002 | Whole-account AI access MUST require explicit informed consent and MUST exclude private spaces categorically. | P0 | Consent describes eligible data types and actions before authorization; private data cannot be included by configuration error or prompt injection. |
| PRD-PRIV-003 | User content MUST remain until the user deletes it; Memdot MUST NOT expire canonical user content merely because it is old or inactive. | P0 | Retention controls distinguish user content from content-free security records and temporary processing artifacts. |
| PRD-PRIV-004 | Users MUST be able to export originals and portable canonical data, and delete an item, conversation, space, or account without later resurrection. | P0 | Deleted content becomes immediately inaccessible and enters visible deletion processing across derived stores/backups. |
| PRD-PRIV-005 | Product analytics and research-content donation MUST be separate opt-ins and off by default; session replay and prompt/content analytics are prohibited in v1. | P0 | Declining analytics does not reduce product functionality; operational telemetry contains no source, prompt, answer, or document content. |
| PRD-PRIV-006 | Provider egress, BYOK behavior, storage location, and deletion limitations MUST be disclosed in plain language. | P0 | A user can identify which external processor may receive content before enabling or using it. |

### 6.6 Platform, language, accessibility, and open source

| ID | Requirement | Priority | Product acceptance |
|---|---|---:|---|
| PRD-PLAT-001 | V1 MUST be a responsive installable PWA usable on desktop and mobile web. | P0 | Core journeys work at supported viewport sizes and meet documented browser support. |
| PRD-PLAT-002 | Offline v1 MUST support explicitly pinned reading and downloaded review packs, but not editing, import, Ask, MCP, or sync-dependent actions. | P1 | Offline state is visible; queued attempt events replay idempotently after reconnect. |
| PRD-PLAT-003 | UI copy MUST launch in English; ingestion, OCR, exact/semantic retrieval, and citations MUST support English, Hindi, and Hinglish for the defined production corpus. | P0 | Mixed-language benchmark gates pass; unsupported scripts/handwriting are labeled beta or experimental. |
| PRD-PLAT-004 | Core workflows MUST meet WCAG 2.2 AA expectations, including keyboard and screen-reader operation. | P0 | Automated and manual accessibility acceptance gates cover authentication, ingestion, Ask, Test, Review, proposals, and consent. |
| PRD-PLAT-005 | Memdot MUST be Apache 2.0 and fully self-hostable with feature parity through replaceable storage, retrieval, identity, encryption, and model providers. | P0 | The release passes required cross-document scenarios with Tex disabled and no hosted-only product gate. |
| PRD-PLAT-006 | Public data contracts MUST be documented and versioned so users can migrate, rebuild indexes, and integrate without private implementation knowledge. | P0 | Export and APIs use stable versioned schemas with compatibility policy. |

### 6.7 Beta and operational product behavior

| ID | Requirement | Priority | Product acceptance |
|---|---|---:|---|
| PRD-BETA-001 | Hosted v1 MUST be a public free beta for eligible adults and MUST NOT advertise a monthly per-user usage quota. | P0 | Eligible users can enroll without payment or invite; marketing and in-product copy do not promise infinite capacity. |
| PRD-BETA-002 | Memdot MUST enforce file-size, request-rate, concurrency, abuse, and system-safety controls independently of the no-advertised-quota policy. | P0 | Controls are documented as safety/availability limits, return actionable states, and are not silently presented as billing quotas. |
| PRD-BETA-003 | Capacity pressure MUST queue, slow, or temporarily refuse work without losing canonical input, duplicating revisions, or returning fabricated success. | P0 | Accepted work has a durable status; refused work identifies whether and when retry is safe. |
| PRD-BETA-004 | Beta status, experimental formats, provider degradation, and incomplete captures MUST be visible at the point they affect trust. | P0 | Users are never led to believe an incomplete source, capture, citation, or index is complete. |
| PRD-OPS-001 | Long-running ingestion, sync, export, deletion, and rebuild work MUST expose durable status and safe retry behavior. | P0 | Refreshing or reconnecting does not lose status; duplicate requests do not duplicate canonical effects. |
| PRD-OPS-002 | User-visible failures MUST distinguish invalid input, unsupported content, permissions, capacity, dependency outage, partial success, and internal failure. | P0 | Every failure state has a safe next action and reference ID when support may be needed. |
| PRD-OPS-003 | Tex or a model-provider outage MUST degrade affected semantic/AI features while preserving exact access, canonical data, privacy, and self-hosted operation. | P0 | Failure never broadens authorization or blocks export/deletion; OSS retrieval supplies the documented fallback. |
| PRD-OPS-004 | Product health and quality MUST be measurable without recording user content in analytics. | P0 | Release gates use synthetic/consented benchmark data and content-free operational events. |

## 7. V1 scope by surface

| Surface | Included in v1 |
|---|---|
| Identity | Hosted Google sign-in, 18+ confirmation, self-host OIDC/operator bootstrap contract. |
| Today | Due review, course state, weak prerequisites/conflicts, import issues, memory proposals. No XP/streak-first design. |
| Library | Files, paste, rich documents, Notion sources, revisions, processing, citations, trash. |
| Spaces | General, Learning, and private spaces for individuals. |
| Rich documents | Headings, lists, tasks, callouts, code, math, tables, media, embeds, backlinks, citations, slash commands, revision history, proposed AI patches. |
| Ask | Scoped source-first chat, citations, external-knowledge labels, conflicts, context receipt. |
| Test | MCQ, short-answer, explain/apply, confidence-before-feedback, sealed answer. |
| Review | FSRS item scheduling, due reasons, filters, offline downloaded packs. |
| Memory | Proposed, approved/stored items, learner evidence, activity, conflicts, provenance. |
| Integrations | Notion, managed AI, optional BYOK, MCP client authorization/revocation. |
| Portability | REST/MCP contracts, account export, complete Docker self-host path. |

## 8. V2 candidates and explicit non-goals

### 8.1 V2 candidates

- selected Google Drive folder sync and broader source connectors;
- Calendar and Tasks synchronization;
- institutions, team spaces, sharing, and role administration;
- guardian/institution flows for users under 18, subject to legal and safety design;
- native mobile applications and richer offline editing;
- audio/video ingestion, browser capture, and controlled URL ingestion;
- additional Indian-language UI and production OCR after corpus gates;
- optional learner-model experiments such as BKT only if they are explainable, calibrated, and beat the simple evidence baseline;
- public plugin/connector SDK and additional portable memory clients.

### 8.2 Non-goals for v1

- a Notion replacement, general-purpose databases, wikis for teams, or real-time collaboration;
- autonomous agents that silently mutate canonical memory;
- passive surveillance of external AI conversations;
- a global force-directed graph as primary navigation;
- automated claims of knowledge based on reading time, chat volume, or self-confidence;
- full handwriting, proof, program, or symbolic-math grading guarantees;
- arbitrary web crawling, audio/video transcription, email/calendar ingestion, or Google Drive sync;
- payments, advertised paid tiers, institutions, teams, children, parental consent, or targeted advertising;
- guaranteed consumer Gemini custom-MCP availability in India;
- rebuilding Tex or depending on private Tex internals;
- hidden hosted-only features unavailable to self-hosters.

## 9. Competitive frame

The competitor set validates individual features but not Memdot’s combined contract:

| Category/example | Established strength | Memdot’s required distinction |
|---|---|---|
| NotebookLM | Source-grounded notebooks and generated learning artifacts | Durable cross-space evidence ledger, portable governed MCP, revisions, and learner evidence across tools. |
| RemNote | Guided learning, flashcards, and mastery/review workflows | General memory first, immutable provenance, multi-client context receipts, and evidence separated from source truth. |
| Anki | Mature spaced repetition | Source/version-aware assessment items, course mapping, context compilation, and broader personal memory. |
| Heptabase | Visual knowledge work and AI/MCP access | Syllabus-tree-first learning, explicit evidence states, source conflicts, private-space boundary, and rebuildable projections. |
| Notion | Flexible authored workspaces and integrations | Evidence-preserving import, learning loop, source-aware retrieval, and constrained AI write proposals rather than workspace replacement. |
| Generic RAG | Semantic retrieval over chunks | Exact + semantic + temporal + graph routing, canonical authorization/version checks, conflicts, and inspectable receipts. |

Memdot must not claim uniqueness for uploads, chat, quizzes, graphs, or spaced repetition individually. Differentiation is demonstrated only when provenance, context compilation, learning evidence, and portable access work together.

Primary comparison references: [RemNote Guided Learn](https://help.remnote.com/en/articles/15724936-guided-learn-mode), [NotebookLM quizzes](https://support.google.com/notebooklm/answer/16958963), [Heptabase MCP](https://support.heptabase.com/en/articles/12679581-how-to-use-heptabase-mcp), and [Anki manual](https://docs.ankiweb.net/getting-started.html).

## 10. Success metrics

### 10.1 North star

**Source-grounded delayed success on novel items (SGDS):** the percentage of eligible, delayed, unhinted assessment responses to previously unseen or materially transformed items that are graded correct and whose feedback is supported by the learner’s current eligible source revisions.

SGDS MUST be segmented by course, question type, language, delay band, and confidence; it MUST NOT include revealed answers, substantive hints, post-feedback captures, duplicate items, or uncertain machine grades.

### 10.2 Product and trust metrics

| Metric | Beta interpretation |
|---|---|
| Activation | Adult completes onboarding, imports or authors one source, receives one valid citation, and completes one eligible test attempt. |
| Grounded answer rate | Answers with complete claim-to-source support and correct locators. Release gate, not an engagement vanity metric. |
| Retrieval success | Exact and semantic tasks meeting the frozen evaluation corpus thresholds. |
| Proposal control | Approval/edit/rejection rates plus zero silent canonical AI writes. |
| Context transparency | Percentage of AI contexts with valid, inspectable receipts. Target: 100%. |
| Learning integrity | Percentage of demonstrated transitions backed by eligible events. Target: 100%. |
| Portable-memory success | Successful authorized MCP search/fetch/context tasks with zero private-space exposure. |
| Ingestion trust | Sources with complete/partial/failure status accurately represented; no silently omitted pages. |
| Deletion integrity | Deletes removed from live retrieval immediately and never resurrected after rebuild/restore. Target: 100%. |
| Sustainable beta | Queue age, provider spend, abuse rate, and failure rate remain within operating guardrails without inventing a hidden user quota. |

Full thresholds and corpus composition belong to [Evaluation and Release Gates](../technical/EVALUATION_RELEASE_GATES.md).

## 11. Public free beta policy

“No advertised monthly quota” means Memdot does not present a recurring per-user allowance or charge during v1 beta. It does not mean unbounded resource use. The product may enforce:

- maximum file and request sizes;
- per-account and per-IP request rates;
- concurrency and queue limits;
- malware, abuse, scraping, denial-of-service, and cost-anomaly controls;
- temporary provider- or system-wide circuit breakers;
- fair-use review and account suspension under published terms.

The UI must distinguish **rejected before acceptance** from **accepted and queued**. Once Memdot accepts canonical input, safety controls cannot silently discard it. The product may degrade from AI synthesis to exact/source access, but privacy, export, deletion, and current job status remain available.

## 12. Privacy, portability, and OSS promises

- User content remains until user deletion; inactivity alone is not deletion.
- Private spaces never cross the external-client boundary.
- Analytics/content research consent is not bundled with service consent.
- AI provider egress is disclosed before use.
- Exports include originals, authored content, canonical structured data, provenance, and documented history in portable formats.
- Apache 2.0 applies to Memdot-owned code. Dependency and model licenses pass a release gate.
- Hosted convenience does not create a product capability unavailable to self-hosters.
- Tex is optional and replaceable. PostgreSQL/object storage remain authoritative; the local retrieval lane can operate without Tex. Tex’s own public migration guidance says applications should retain an authoritative log rather than use Tex as an audit store: [Tex guidance](https://github.com/metacoglabs/docs/blob/852c4cf105df58e488a1e9e8a877e3a4524dd113/migration/from-redis.mdx#L78-L83).

The detailed threat model and policy boundaries are in [Security, Privacy, and Threat Model](../technical/SECURITY_PRIVACY_THREAT_MODEL.md).

## 13. Launch risks and dependencies

| Risk/dependency | Product impact | Required mitigation or gate |
|---|---|---|
| Citation or parser errors | Users may trust unsupported answers or incomplete sources. | Golden multilingual corpus, visible partial/low-confidence state, locator tests, and no “complete” state with silently omitted pages. |
| Cross-account/private leakage | Catastrophic trust and privacy failure. | Deny-by-default authorization, RLS, canonical result rejoin, adversarial MCP tests, and zero-leak launch gate. |
| Tex API instability or isolation uncertainty | Retrieval correctness, deletion, or tenancy may be unsafe. | Contract-test stable IDs, tenancy, retries, deletion, citations, latency, and outage behavior; default to OSS lane until passed. |
| Model/provider egress | Unexpected data region or retention. | India-region verification, direct adapters, explicit disclosure, BYOK clarity, and content-free telemetry. |
| Notion live semantics | Duplicate content, expiring assets, or destructive sync. | Live authorized-workspace spike, exact snapshots, dedicated write root, conflict review, and reconciliation. |
| Learning-model overclaim | False confidence and harmful prioritization. | Explainable evidence states, sealed tests, deterministic eligibility rules, and no BKT/mastery black box in v1. |
| Open free beta abuse/cost | Queue pressure or unsustainable inference spend. | Safety limits, fair scheduling, circuit breakers, managed-model routing, and transparent degraded states. |
| India adult-only compliance | Ineligible users or unclear consent. | Legal review before beta, 18+ confirmation, no targeted advertising, and no child-oriented launch claims. |
| Empty starting codebase | Docs may drift from eventual paths/commands. | Codebase Context Map marks target paths; implementation scaffold must update maps and validation commands. |

## 14. V1 launch acceptance

V1 is launchable only when the package’s evaluation gates pass and these end-to-end outcomes are demonstrated:

1. Google signup and 18+ confirmation block ineligible onboarding.
2. Public free enrollment works without payment or an advertised monthly quota, while safety controls return honest states.
3. File and Notion ingestion preserve deterministic revisions and working citations.
4. Rich documents preserve block/revision identity and AI edits remain proposed.
5. Ask is source-first, labels external knowledge, exposes conflicts, and supplies a context receipt.
6. Authorized external clients retrieve the entire eligible non-private account; private-space leakage is zero.
7. External interaction capture is explicitly complete/partial/unavailable and never passively inferred.
8. Memory proposals require approval.
9. Map, Test, evidence update, and Review work with sealed answers and eligible event rules.
10. Tex outage preserves canonical data, exact access, authorization, export/deletion, and documented OSS fallback quality.
11. Historical versions and source conflicts remain distinguishable.
12. Offline pinned reading and downloaded review replay without cross-account cache leakage.
13. Export and deletion complete without resurrection after a projection rebuild or backup restore.
14. The full test suite passes in a Tex-disabled Docker self-host deployment.

## 15. Requirement traceability

The [Functional Specification](./FSD.md) defines visible flows and acceptance scenarios. The [Technical Requirements Document](../technical/TRD.md) owns implementation contracts. The [System Architecture](../technical/SYSTEM_ARCHITECTURE.md) owns boundaries and flows. Accepted decisions live in [`docs/adr/`](../adr/).

| PRD family | FSD ownership | Technical ownership | Primary ADR themes |
|---|---|---|---|
| PRD-CORE-* | FSD-LIB, FSD-SPC, FSD-DOC, FSD-SRC, FSD-MEM | Canonical data, document, ingestion, search, revision contracts | Evidence Ledger; parser-neutral model; Tiptap schema |
| PRD-LEARN-* | FSD-CRS, FSD-ASK, FSD-TST, FSD-REV | Learning ledger, assessment, scheduler, retrieval contracts | Learning mode; Evidence Twin and FSRS |
| PRD-AI-* | FSD-ASK, FSD-DOC, FSD-MEM, FSD-INT | Context compiler, model adapter, proposal contracts | Context receipts; proposed writes; regional inference |
| PRD-INT-* | FSD-INT, FSD-NOT, FSD-MEM | MCP, OAuth, interaction, connector contracts | Whole-account MCP; interaction capture; Notion area |
| PRD-PRIV-* | FSD-AUTH, FSD-INT, FSD-EXP, FSD-SET | Authorization, retention, export/delete, audit contracts | Private boundary; India hosting; canonical ledger |
| PRD-PLAT-* | FSD-NAV, FSD-OFF, FSD-A11Y | PWA, local cache, deployment, provider contracts | OSS parity; offline boundary |
| PRD-BETA-* | FSD-ERR, FSD-ING, FSD-SET | Rate safety, queues, idempotency, capacity contracts | Reversible/provider-independent architecture |
| PRD-OPS-* | FSD-ERR plus every async surface | Workflow, observability, fallback, recovery contracts | Canonical state; replaceable Tex |

## 16. Change control

- Changing any P0 requirement, private-space behavior, learning evidence rule, deletion promise, OSS parity promise, or public-interface scope requires a superseding PRD revision and an ADR.
- Requirement IDs are never renumbered after implementation begins.
- A requirement removed from scope is marked `Retired` with the replacement or rationale; its ID is not reused.
- FSD, TRD, architecture, security, evaluation, and Codebase Context Map changes must accompany any product change that invalidates their traceability.
