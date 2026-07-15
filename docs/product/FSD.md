# Memdot Functional Specification Document

**Status:** Approved functional contract for v1 implementation
**Audience:** Founder, product/design, engineering, QA, security, operations, and AI coding agents
**Last updated:** 2026-07-15
**Normative language:** **MUST**, **SHOULD**, and **MAY** describe requirement strength. Requirement IDs are permanent and are not reused.

## 1. Purpose

This document specifies observable v1 behaviour: routes, states, user actions,
business rules, validation, and acceptance scenarios. The [PRD](PRD.md) explains
why the product exists; the [TRD](../technical/TRD.md) owns implementation
contracts; [ADRs](../adr/README.md) own durable architectural choices.

Memdot is a general personal-memory platform with Learning as its first flagship
mode. A hosted v1 user signs in with Google, confirms they are at least 18,
organises memory into Spaces, and may connect an external AI to the complete
eligible non-private account. Private Spaces are an absolute external-AI
exclusion.

## 2. Route and navigation model

| Route | Purpose | Primary states |
|---|---|---|
| `/auth` | Google sign-in | ready, authenticating, denied, failed |
| `/onboarding` | Age confirmation and first setup | age, profile, first Space, first import, complete |
| `/today` | Action-oriented home | ready, empty, partial, degraded |
| `/library` | Canonical sources and authored documents | all, inbox, processing issues, trash |
| `/library/sources/:id` | Source evidence and revisions | processing, ready, ready-with-warnings, failed, unavailable |
| `/spaces` | General and Learning Space directory | active, archived, empty |
| `/spaces/:id` | Space overview | general overview or Learning overview |
| `/spaces/:id/map` | Learning syllabus/evidence map | confirmed, suggested, gaps, conflicts |
| `/spaces/:id/sources` | Sources scoped to one Space | same source states as Library |
| `/documents/:id` | Rich-document reader/editor | clean, saving, dirty, conflicted, proposal preview |
| `/ask` | Native source-first conversation | ready, compiling, answering, partial, degraded |
| `/test` | Test setup/session/results | setup, active, grading, results, provisional |
| `/review` | Due queue/session/results | queue, active, syncing, results, offline-provisional |
| `/memory/proposed` | Review pending AI/external writes | pending, duplicate, conflict, expired |
| `/memory/items` | Approved memory and retained interactions | current, historical, deleted/unavailable |
| `/memory/activity` | Reads, writes, receipts, sync and deletion history | filterable, empty |
| `/integrations` | Notion, MCP clients, model/BYOK | connected, attention, revoked, failed |
| `/settings` | Profile, AI, privacy, offline, export, deletion | ready, saving, re-auth-required |

Global search and the command palette are overlays available from every
authenticated online route. Source/citation and evidence details use a reusable
right-side inspector on desktop and a full-height sheet on smaller screens.

### Navigation requirements

| ID | Requirement | Drivers |
|---|---|---|
| FSD-NAV-001 | The authenticated primary navigation MUST expose Today, Library, Spaces, Ask, Test, Review, Memory, Integrations, and Settings in that order. | PRD-CORE-001, PRD-LEARN-001 |
| FSD-NAV-002 | The top bar MUST expose global search/command palette, `Add`, processing/sync status, online/offline state, and account controls. | PRD-CORE-002, PRD-OPS-001 |
| FSD-NAV-003 | A route opened from a Space/source/concept MUST preserve that context in breadcrumbs and relevant action defaults. | PRD-LEARN-002 |
| FSD-NAV-004 | Browser refresh, deep link, and back/forward navigation MUST preserve canonical route state; unsaved online document state receives an explicit leave warning. | PRD-PLAT-001, PRD-OPS-001 |
| FSD-NAV-005 | A status badge MUST distinguish beta, experimental feature, partial data, stale offline snapshot, and service degradation; those concepts cannot share one ambiguous warning. | PRD-BETA-004 |

## 3. Global state language

Every data-bearing surface uses the following explicit states rather than
inferring state from missing/null fields.

| State | Meaning | Required presentation |
|---|---|---|
| Loading | Initial request is in progress | Layout-preserving skeleton and accessible status |
| Empty | Request succeeded with no records | Explanation plus safe primary action |
| Processing | Durable background work exists | Current stage, accepted time, progress when reliable, safe navigation |
| Partial | Some expected content is unavailable | What is present, what is missing, and impact |
| Degraded | A provider/lane is unavailable but safe fallback exists | Affected capability and retry/status action |
| Failed | Operation reached a terminal failure | Safe detail, correlation ID, retryability, next action |
| Unauthorized | Current actor/grant lacks access | Reconnect/re-auth or return action without resource disclosure |
| Unavailable | Historical/deleted/revoked resource cannot be opened | Reason when safe and recovery/export option if applicable |
| Offline | Network-dependent action is unavailable | Cached timestamp, supported offline actions, reconnect action |
| Conflicted | Two valid versions require a user decision | Both versions/base, consequences, no implicit winner |

| ID | Requirement | Drivers |
|---|---|---|
| FSD-ERR-001 | Every failure MUST use one stable category: invalid input, unsupported content, permissions, safety limit, capacity, dependency outage, partial success, conflict, or internal failure. | PRD-OPS-002 |
| FSD-ERR-002 | User-visible failures MUST provide a safe next action and a correlation ID when operator support may be required; stack traces and provider IDs are prohibited. | PRD-OPS-002 |
| FSD-ERR-003 | A private, deleted, or unauthorized item addressed by opaque ID MUST use the same not-found presentation to prevent enumeration. | PRD-PRIV-002 |
| FSD-ERR-004 | Accepted durable work MUST never disappear on refresh. Refused work MUST clearly state that it was not accepted. | PRD-BETA-003, PRD-OPS-001 |
| FSD-ERR-005 | Capacity controls MUST present queued, retry-after, or temporarily unavailable states and MUST NOT be described as a monthly billing quota. | PRD-BETA-001, PRD-BETA-002 |
| FSD-ERR-006 | Partial/degraded answers MUST remain visibly marked in the answer, citation panel, and context receipt. | PRD-AI-004, PRD-BETA-004 |

## 4. Authentication and onboarding

### 4.1 Hosted Google authentication

| ID | Requirement | Drivers |
|---|---|---|
| FSD-AUTH-001 | Hosted `/auth` MUST offer Google sign-in as the only v1 login method. Email/password, magic link, and invite code UI are absent. | PRD-PRIV-001 |
| FSD-AUTH-002 | Successful Google authentication MUST continue to age confirmation before creating an active Memdot account. | PRD-PRIV-001 |
| FSD-AUTH-003 | Authentication cancellation, blocked popup, provider denial, session expiry, and internal failure MUST be separately recoverable. | PRD-OPS-002 |
| FSD-AUTH-004 | Sensitive actions—external-AI grant, connector/model credential change, export, and deletion—MUST require recent Google re-authentication. | PRD-PRIV-002, PRD-PRIV-004 |
| FSD-AUTH-005 | Logout MUST revoke the browser session and clear account-scoped offline data on that device. | PRD-PRIV-002, PRD-PLAT-002 |

Self-hosted deployments replace the Google-only screen with operator-configured
OIDC and an operator bootstrap path. The hosted product copy must not imply that
Google owns or processes self-hosted content.

### 4.2 Adult confirmation and first setup

| ID | Requirement | Drivers |
|---|---|---|
| FSD-ONB-001 | The user MUST explicitly confirm `I am 18 or older` before account activation; v1 MUST NOT request a birth date or identity document. | PRD-PRIV-001 |
| FSD-ONB-002 | A user who cannot confirm MUST be told that v1 is adults-only and MUST NOT enter or store product content. | PRD-PRIV-001 |
| FSD-ONB-003 | Onboarding MUST set display name, timezone, English UI, and optional content-language hints for English, Hindi, or Hinglish. | PRD-PLAT-003 |
| FSD-ONB-004 | Onboarding MUST offer a General Space or Learning Space; Learning asks for course name, optional institution/board, term, exam date, and syllabus/source. | PRD-CORE-001, PRD-LEARN-001 |
| FSD-ONB-005 | Initial import and AI connection MUST be skippable. Users can reach an empty Today screen without uploading or connecting an external service. | PRD-CORE-001 |
| FSD-ONB-006 | Public beta signup MUST require neither payment nor invite. It MUST display beta status without promising infinite capacity or permanence of experimental features. | PRD-BETA-001, PRD-BETA-004 |

## 5. Today

Today is an action surface, not a vanity dashboard.

| ID | Requirement | Drivers |
|---|---|---|
| FSD-TOD-001 | Today MUST present one primary `Do next` action selected from due review, incomplete setup, processing repair, unresolved conflict, or pending memory proposal. | PRD-LEARN-005, PRD-OPS-002 |
| FSD-TOD-002 | Learning cards MUST show source coverage, evidence coverage, due/lapsed count, exam date when present, and the reason behind the recommendation. | PRD-LEARN-001, PRD-LEARN-005 |
| FSD-TOD-003 | Today MUST surface imports needing repair, unconfirmed map suggestions, source conflicts, integration failures, and pending proposals without treating them as learner failure. | PRD-BETA-004 |
| FSD-TOD-004 | Streaks, XP, leaderboards, and study-time celebrations MUST NOT be primary v1 metrics or navigation. | PRD-LEARN-007 |
| FSD-TOD-005 | A new account's empty state MUST offer Create Space, Add source, Create note, and Explore Learning with concise explanations. | PRD-CORE-001 |

## 6. Library and source detail

### 6.1 Library

| ID | Requirement | Drivers |
|---|---|---|
| FSD-LIB-001 | Library MUST provide All, Inbox, Processing issues, and Trash views. | PRD-CORE-002 |
| FSD-LIB-002 | Users MUST be able to filter by Space, course, source type, import origin, current/historical state, processing state, language, and label. | PRD-CORE-003 |
| FSD-LIB-003 | Each row MUST show title, type, owning Space/course, origin, current revision time, processing/sync state, and private-space indicator. | PRD-CORE-002, PRD-PRIV-002 |
| FSD-LIB-004 | Bulk actions in v1 are move to Space, archive, restore, export, reprocess, and delete. Bulk AI mutation is excluded. | PRD-CORE-001, PRD-PRIV-004 |
| FSD-LIB-005 | Search results MUST distinguish source, authored document, approved memory, conversation, completed attempt, curriculum item, and historical revision. | PRD-CORE-003, PRD-CORE-006 |

### 6.2 Source detail

| ID | Requirement | Drivers |
|---|---|---|
| FSD-SRC-001 | Source detail MUST show original/current content, extracted outline, current revision, version history, linked concepts, citations, processing quality, and sync origin. | PRD-CORE-002, PRD-CORE-003 |
| FSD-SRC-002 | A citation open MUST focus the exact page region, block, table cell, formula, line, or conversation turn and identify its immutable revision. | PRD-AI-001 |
| FSD-SRC-003 | Historical revisions MUST display a persistent historical banner and a route to the current revision; historical content cannot look current. | PRD-CORE-005 |
| FSD-SRC-004 | Conflicting source claims MUST show all eligible statements, authority/origin, effective/revision time, and unresolved/resolved state. | PRD-CORE-005 |
| FSD-SRC-005 | `Ask this source`, `Attach to Space/course`, `Convert to editable note`, `Reprocess`, `Export`, and `Delete` MUST preserve source revision/provenance semantics. | PRD-CORE-002, PRD-CORE-003 |
| FSD-SRC-006 | `Convert to editable note` MUST preview unsupported/lossy mappings. The new document links to the source but never mutates the imported revision. | PRD-CORE-004 |
| FSD-SRC-007 | A ready-with-warnings source MUST identify affected pages/elements and whether Ask/Test can rely on them; it cannot be labelled simply Ready. | PRD-BETA-004 |

## 7. Spaces and Learning map

| ID | Requirement | Drivers |
|---|---|---|
| FSD-SPC-001 | Users MUST be able to create, rename, archive, restore, and delete General or Learning Spaces. Every item has one primary owning Space in v1. | PRD-CORE-001 |
| FSD-SPC-002 | Space settings MUST show external-AI visibility as `Eligible` or `Private`. `Private` categorically excludes the Space from all external MCP reads and write targets. | PRD-PRIV-002, PRD-INT-001 |
| FSD-SPC-003 | Marking a Space Private MUST take effect for the next external request and warn that previously disclosed content cannot be recalled from an AI provider. | PRD-PRIV-002 |
| FSD-SPC-004 | Changing Private to Eligible MUST require explicit confirmation that the whole connected-account read grant now includes the Space. | PRD-PRIV-002 |
| FSD-SPC-005 | A Learning Space overview MUST show courses, exam dates, source/evidence coverage, due/lapsed concepts, unconfirmed suggestions, recent tests/reviews, and next action. | PRD-LEARN-001 |
| FSD-SPC-006 | The default Map MUST be a stable Course → Unit → Objective → Concept tree; selecting a concept may show only local prerequisites, dependants, sources, evidence, and recall state. | PRD-LEARN-001 |
| FSD-SPC-007 | Every suggested node/edge MUST show origin, confidence, supporting citation, and confirmation status. Suggested prerequisites cannot block study progression. | PRD-LEARN-001 |
| FSD-SPC-008 | Confirmed prerequisite edges MUST remain acyclic. A user action that creates a cycle is rejected with the specific cycle path. | PRD-LEARN-001 |
| FSD-SPC-009 | A concept MUST show three independent indicators: source coverage, evidence state, and recall state; no aggregate mastery number may replace them. | PRD-LEARN-004 |

## 8. Rich-document authoring

V1 supports rich documents, not databases or real-time collaboration.

| ID | Requirement | Drivers |
|---|---|---|
| FSD-DOC-001 | The editor MUST support paragraphs, headings, lists, tasks, quotes, callouts, code, inline/block math, tables, images/files, allowlisted embeds, links, highlights, entity references, citation references, and slash commands. | PRD-CORE-004 |
| FSD-DOC-002 | Each addressable block MUST keep a stable block ID across normal edits. Copy/paste or duplication creates new IDs unless explicitly inserting a reference. | PRD-CORE-004 |
| FSD-DOC-003 | Online editing MUST show clean, dirty, saving, saved, disconnected-dirty-buffer, stale-base, and failed-save states. | PRD-OPS-002 |
| FSD-DOC-004 | Saves MUST use the current base revision. A stale base MUST never overwrite; the UI offers reload, copy as new document, or explicit reviewed merge. | PRD-CORE-004 |
| FSD-DOC-005 | Revision history MUST show author/origin, timestamp, change source, proposal link, and a readable diff. Restoring creates a new revision rather than deleting history. | PRD-CORE-005 |
| FSD-DOC-006 | AI actions MUST create a source-cited patch proposal against one base revision. The preview shows inserted/replaced/deleted/moved blocks and supports accept, reject, or edit. | PRD-AI-003 |
| FSD-DOC-007 | A proposal whose base is no longer current MUST become Conflicted and require rebase/review; acceptance cannot silently target changed text. | PRD-AI-003 |
| FSD-DOC-008 | Unknown/unsupported blocks MUST render a preserved placeholder. Imports/exports MUST report lossy mappings rather than silently drop content. | PRD-CORE-002, PRD-PLAT-006 |
| FSD-DOC-009 | No arbitrary HTML, script, executable code, active SVG, or unapproved iframe may render. Unsupported embeds remain safe links. | PRD-PRIV-002 |
| FSD-DOC-010 | General offline document editing is not a v1 feature. A connection-drop buffer is crash recovery only and submits after reconnect under normal revision checks. | PRD-PLAT-002 |

## 9. Ingestion and processing

| ID | Requirement | Drivers |
|---|---|---|
| FSD-ING-001 | `Add` MUST offer file/image upload, Markdown/TXT, paste, rich note, selected Notion import, General Space, and Learning Space/course creation. Arbitrary URL/audio/video import is absent. | PRD-CORE-002 |
| FSD-ING-002 | Before acceptance, upload UI MUST validate supported type and configured size/page constraints and explain password-protected/unsafe/unsupported cases. | PRD-BETA-002 |
| FSD-ING-003 | An accepted job MUST expose stages: uploaded, validating, parsing, normalizing, mapping, indexing, ready, ready-with-warnings, failed, or deleting. | PRD-OPS-001 |
| FSD-ING-004 | Progress is determinate only when measured; otherwise show current stage and elapsed time, not fabricated percentages. | PRD-BETA-004 |
| FSD-ING-005 | Duplicate bytes/snapshot MUST reuse the existing revision and report the duplicate instead of creating indistinguishable copies. The user may still attach the source to another Space through an explicit reference/move flow. | PRD-CORE-005 |
| FSD-ING-006 | Low OCR/parser confidence MUST identify affected pages/blocks and whether a deep-parser retry is queued, available, or exhausted. | PRD-BETA-004 |
| FSD-ING-007 | Retry resumes or adds an attempt to the same logical job. Reprocess creates a new parse profile/run while retaining the active prior result until promotion. | PRD-OPS-001 |
| FSD-ING-008 | Cancellation stops work not yet committed but never deletes an existing source revision. Delete is a distinct confirmed action. | PRD-PRIV-004 |
| FSD-ING-009 | Queue overload MUST either durably accept and show queue position/estimate when reliable or reject before upload completion with Retry-After guidance. | PRD-BETA-003 |
| FSD-ING-010 | Handwriting and unvalidated regional-script OCR MUST carry Experimental labels in upload, source detail, Ask citations, and evaluation-related use. | PRD-PLAT-003 |

## 10. Notion integration

| ID | Requirement | Drivers |
|---|---|---|
| FSD-NOT-001 | Connecting Notion MUST explain inbound-only sources versus the dedicated two-way Memdot root before OAuth. | PRD-INT-005 |
| FSD-NOT-002 | Setup MUST select/create one Memdot root, select inbound pages/databases, and map each selection to a destination Space before first sync. | PRD-INT-005 |
| FSD-NOT-003 | Selected pages outside the root MUST be visibly read-only from Memdot. No Memdot action may edit, move, archive, or delete those Notion pages. | PRD-INT-005 |
| FSD-NOT-004 | Only an approved Memdot-authored document may be published beneath the root. The publish preview MUST show unsupported/fallback mappings. | PRD-INT-005, PRD-AI-003 |
| FSD-NOT-005 | Documents beneath the root MUST sync edits in both directions using a shared base. Concurrent changes pause that document and show base, Notion, and Memdot versions. | PRD-CORE-005, PRD-INT-005 |
| FSD-NOT-006 | Conflict actions are Keep Notion, Keep Memdot, or Review merge. Every choice creates a new version and preserves the losing version in history. | PRD-CORE-005 |
| FSD-NOT-007 | Integration status MUST show connected account/workspace, selected content, root, destination Spaces, last successful reconciliation, pending/failed work, and revoke. | PRD-INT-005 |
| FSD-NOT-008 | Revocation/disconnect stops future work and removes credentials. Imported/synced Memdot content remains until separately deleted. | PRD-PRIV-003 |
| FSD-NOT-009 | Moved, archived, deleted, inaccessible, rate-limited, unsupported, and partially fetched Notion content MUST have distinct states and safe actions. | PRD-OPS-002 |

## 11. Ask, search, citations, and context receipts

### 11.1 Native Ask

| ID | Requirement | Drivers |
|---|---|---|
| FSD-ASK-001 | Ask MUST keep scope visible while composing and answering. Native choices are whole account, selected Spaces, one Learning course, selected concepts, or selected sources. | PRD-LEARN-002 |
| FSD-ASK-002 | A private Space MAY be used inside native authenticated Ask but MUST display `Private — unavailable to connected AI` and cannot be added to an external-AI handoff. | PRD-PRIV-002 |
| FSD-ASK-003 | The response MUST separate `From your memory`, `External knowledge`, conflicts/uncertainty, and insufficiency. An absent section is not rendered. | PRD-AI-001, PRD-AI-002 |
| FSD-ASK-004 | Every material account-derived claim MUST have an inline citation opening an immutable revision/locator. Unsupported model knowledge MUST be explicitly labeled and uncited-to-memory. | PRD-AI-001, PRD-AI-002 |
| FSD-ASK-005 | When sources conflict, the answer MUST show the disagreement and source/revision authority; the model may not silently choose by retrieval score. | PRD-CORE-005 |
| FSD-ASK-006 | When evidence is insufficient, Ask MUST say what is missing and offer narrower scope, another source, or a labeled external-knowledge answer where policy permits. | PRD-AI-001 |
| FSD-ASK-007 | Every answer MUST offer Open source, Inspect context, Test me, and Propose memory where applicable. `Propose memory` never saves directly. | PRD-AI-003, PRD-AI-004 |
| FSD-ASK-008 | Native conversation turns and associated receipts MUST be retained automatically until the user deletes the conversation/account. | PRD-PRIV-003, PRD-INT-003 |
| FSD-ASK-009 | Provider/model/processing-region disclosure MUST be visible from the answer and context inspector without exposing credentials. | PRD-PRIV-006 |
| FSD-ASK-010 | A degraded retrieval lane MUST not remove citations or privacy checks. The answer and receipt MUST identify degradation and any material omissions. | PRD-OPS-003 |

### 11.2 Context receipt inspector

| ID | Requirement | Drivers |
|---|---|---|
| FSD-ASK-011 | The inspector MUST show purpose/scope, compiler/retrieval policy version, evidence items, revisions, locators, selection reasons, conflicts, omissions, budget use, and degraded lanes. | PRD-AI-004 |
| FSD-ASK-012 | The inspector MUST distinguish the external client/model route from the evidence content and MUST NOT expose hidden chain-of-thought. | PRD-AI-004 |
| FSD-ASK-013 | Deleted or newly private evidence referenced by an old receipt MUST become unavailable and MUST NOT be reconstructed from the receipt. | PRD-PRIV-004 |

### 11.3 Global search

| ID | Requirement | Drivers |
|---|---|---|
| FSD-SRC-008 | Global search MUST support exact phrases/identifiers, semantic queries, type/Space/course filters, and explicit current/historical mode. | PRD-CORE-003 |
| FSD-SRC-009 | Default search MUST return current eligible content. Historical results appear only under explicit history/change intent and carry a historical label. | PRD-CORE-005 |
| FSD-SRC-010 | Result snippets MUST preserve exact matched terminology and identify why the result matched without exposing provider-specific scores as truth. | PRD-CORE-003 |

## 12. Test

| ID | Requirement | Drivers |
|---|---|---|
| FSD-TST-001 | Test setup MUST offer recommended evidence-gap testing, Space/course/concept scope, question count, and supported types: MCQ, short answer, written explain/apply. | PRD-LEARN-003 |
| FSD-TST-002 | One item MUST appear at a time. The immutable prompt/item version and response start time are fixed when displayed. | PRD-LEARN-003 |
| FSD-TST-003 | The learner MUST record confidence (`guessing`, `unsure`, `sure`) before feedback. Confidence cannot change answer correctness. | PRD-LEARN-006 |
| FSD-TST-004 | Hints MUST be explicitly requested and recorded as none, minor, or substantive. A substantive hint makes the attempt ineligible for demonstrated recall. | PRD-LEARN-004 |
| FSD-TST-005 | The sealed answer/rubric MUST remain unavailable to the client and external AI before submit or explicit Reveal answer. | PRD-LEARN-003 |
| FSD-TST-006 | MCQ submission MUST show correctness, rationale, source citation, and confidence calibration. MCQ alone cannot establish delayed demonstration. | PRD-LEARN-004, PRD-LEARN-006 |
| FSD-TST-007 | Short/written answers MUST show grade status `deterministic`, `model-high-confidence`, `provisional`, or `human-reviewed`. Provisional grades cannot establish demonstration. | PRD-LEARN-004 |
| FSD-TST-008 | Reveal answer, skip, substantive hint, post-feedback response, and low-confidence/ungradable response MUST show why evidence is practice-only. | PRD-LEARN-004 |
| FSD-TST-009 | Results MUST show corrections, citations, confidence-versus-correctness, evidence changes with receipts, and scheduled reviews. | PRD-LEARN-004, PRD-LEARN-006 |
| FSD-TST-010 | A user MUST be able to report an ambiguous/bad item; it becomes review-blocked without deleting the attempt history. | PRD-LEARN-003 |
| FSD-TST-011 | Tests whose source/item revisions retire during an active session may finish, but results MUST identify retirement and cannot create new future items from the retired version. | PRD-CORE-005 |

## 13. Review

| ID | Requirement | Drivers |
|---|---|---|
| FSD-REV-001 | Review landing MUST show due count, estimated time, course filters, due reason, and ordering: lapsed/due prerequisites, overdue, new-with-confirmed-prerequisites, then pinned. | PRD-LEARN-005 |
| FSD-REV-002 | Review session MUST be one item at a time with response, confidence, optional hint, feedback, source, `Why am I seeing this?`, and Report item. | PRD-LEARN-005 |
| FSD-REV-003 | The normal user MUST NOT configure FSRS parameters in v1. The reason inspector shows prior eligible event, current state, and due window in understandable language. | PRD-LEARN-005 |
| FSD-REV-004 | Rating mapping MUST be explained when relevant: Again for incorrect/skipped/revealed/substantive hint, Hard for correct with scaffold/minor error, Good for unhinted correct, Easy only when explicitly effortless. | PRD-LEARN-005 |
| FSD-REV-005 | Review summary MUST show recalled, lapsed, next due, evidence updates, provisional/ungraded items, and concepts needing explanation/test. | PRD-LEARN-005 |
| FSD-REV-006 | Offline review uses only a downloaded seven-day pack. Responses remain `Pending sync`; no authoritative evidence/FSRS change is shown before server acknowledgement. | PRD-PLAT-002 |
| FSD-REV-007 | Replayed offline attempts MUST deduplicate by client event ID; a conflict or retired item receives explicit reconciliation instead of duplicate evidence. | PRD-OPS-001 |

## 14. Memory

Memory has Proposed, Stored, and Activity tabs.

| ID | Requirement | Drivers |
|---|---|---|
| FSD-MEM-001 | Proposed MUST include AI answers, external agents, document patches, import-derived claims, and conflict-resolution suggestions with origin, target, truth class, citations, duplicate/conflict status, and age. | PRD-AI-003 |
| FSD-MEM-002 | Actions are Approve, Edit and approve, Reject, and Delete pending. Approval creates a new canonical version; rejection changes no source/learner evidence. | PRD-AI-003 |
| FSD-MEM-003 | Pending/expired/rejected proposals MUST be excluded from ordinary search, Ask, external MCP reads, and learner evidence. | PRD-AI-003 |
| FSD-MEM-004 | Stored MUST distinguish source assertion, user assertion, approved derived memory, external knowledge, conversation episode, and learner evidence. | PRD-CORE-006 |
| FSD-MEM-005 | Stored-item detail MUST show current/history, origin, citations, related entities/concepts, conflict state, projection/index health, last-use receipts, and edit/suppress/delete/reindex actions as applicable. | PRD-CORE-006 |
| FSD-MEM-006 | Editing an approved memory MUST create a revision. Deleting/suppressing MUST update canonical eligibility before projections and never leave stale external visibility. | PRD-PRIV-004 |
| FSD-MEM-007 | Activity MUST show first-party/external reads, proposals/decisions, interaction capture, exports, sync, privacy changes, deletion, provider degradation, and rebuilds with content-minimised metadata. | PRD-AI-004, PRD-PRIV-005 |
| FSD-MEM-008 | Captured external conversations MUST show source client and completeness (`single turn`, `partial thread`, `complete import`, or `unknown`). Missing turns cannot be represented as complete. | PRD-INT-003 |
| FSD-MEM-009 | A user may mark a conversation as practice, confusion, insight, or candidate evidence. It may affect priority but cannot establish demonstration unless a pre-feedback response independently meets all test eligibility rules. | PRD-LEARN-004 |

## 15. Integrations and external AI

Integrations separates Source imports, AI access, and Export/sync.

| ID | Requirement | Drivers |
|---|---|---|
| FSD-INT-001 | Each connection card MUST show provider/client, connection type, granted actions, whole-account/private-space policy, last access/sync, capture completeness, failures, and Revoke. | PRD-INT-004 |
| FSD-INT-002 | External AI consent MUST plainly state that `memdot.memory.read` covers all current/future non-private Spaces, including relevant retained chats and completed attempts. No per-Space/data-class read selector appears in v1. | PRD-INT-001, PRD-PRIV-002 |
| FSD-INT-003 | Consent MUST state that Private Spaces, sealed answer keys, secrets, pending proposals, and incomplete attempts remain excluded and that returned data cannot be clawed back from the downstream provider. | PRD-PRIV-002 |
| FSD-INT-004 | Read, propose-memory, and record-interaction grants MUST be displayed separately. Declining write grants MUST leave read-only connection usable. | PRD-INT-002 |
| FSD-INT-005 | Revocation MUST take effect for the next request and show success/failure. Previously captured interactions or receipts remain account content until separately deleted. | PRD-INT-004 |
| FSD-INT-006 | The product MUST explain that MCP cannot passively observe a host's complete chat and MUST never advertise guaranteed universal conversation capture. | PRD-INT-003 |
| FSD-INT-007 | `record_interaction` activity MUST show explicitly supplied turns, idempotent replay, target non-private Space, context receipt when present, and declared completeness. It never updates learning evidence automatically. | PRD-INT-002, PRD-LEARN-004 |
| FSD-INT-008 | BYOK/provider setup MUST disclose provider, processing region, retention/training controls, credential owner, and deletion limitations before testing/saving the key. | PRD-PRIV-006 |
| FSD-INT-009 | A provider outage MUST show which native/external features are affected. Source browsing, exact/local retrieval, export, deletion, and privacy controls remain accessible where canonical services are healthy. | PRD-OPS-003 |

## 16. Settings

| ID | Requirement | Drivers |
|---|---|---|
| FSD-SET-001 | Profile MUST show Google identity, display name, timezone, English UI, and English/Hindi/Hinglish content-language preferences. Hosted v1 has no password controls. | PRD-PRIV-001, PRD-PLAT-003 |
| FSD-SET-002 | AI settings MUST show managed provider default, enabled BYOK adapters, provider/region policy, and a route to revoke/delete credentials. | PRD-AI-005, PRD-PRIV-006 |
| FSD-SET-003 | Privacy MUST show connected AI clients, Private Spaces, analytics opt-in (off), research donation consent (off), retained conversations, and content-free audit explanation. | PRD-PRIV-002, PRD-PRIV-005 |
| FSD-SET-004 | Offline settings MUST show installed-PWA state, pinned content, review-pack age/expiry, storage use, per-device removal, and clear-all action. | PRD-PLAT-002 |
| FSD-SET-005 | Export and deletion MUST be distinct. No v1 Billing page, payment method, monthly allowance meter, or upgrade paywall is shown. | PRD-BETA-001, PRD-PRIV-004 |
| FSD-SET-006 | Safety limits MAY be explained at the point they apply and in service status/help; they MUST NOT be framed as paid-plan quotas. | PRD-BETA-002 |

## 17. Export, deletion, and recovery

| ID | Requirement | Drivers |
|---|---|---|
| FSD-EXP-001 | Users MUST be able to export an item, conversation, Space, or complete account after recent re-authentication. Export is a durable job with status and expiring download. | PRD-PRIV-004 |
| FSD-EXP-002 | Account export MUST include originals, revisions/provenance, MemdotDocument JSON, best-effort Markdown/HTML, assets, approved memories, conversations/capture status, course graph, learner events, citations, and a hash manifest/warnings. | PRD-PLAT-006 |
| FSD-EXP-003 | Delete item/conversation/Space/account MUST show scope, immediate visibility/revocation effect, live purge target, backup expiry, and irreversible consequences before confirmation. | PRD-PRIV-004 |
| FSD-EXP-004 | Deletion MUST hide affected content immediately and expose progress for canonical, object, connector, Tex/local projection, and backup stages without exposing internal provider IDs. | PRD-PRIV-004 |
| FSD-EXP-005 | An in-progress deletion cannot be cancelled after irreversible purge begins. Failure shows retry/operator escalation while the tombstoned content remains unavailable. | PRD-OPS-001 |
| FSD-EXP-006 | A restored backup MUST apply deletion history before serving content; a deleted item must never reappear as current, searchable, or syncable. | PRD-PRIV-004 |
| FSD-EXP-007 | Notion disconnect/deletion MUST separately explain credential revocation, future-sync stop, imported-content retention, and optional content deletion. | PRD-INT-005 |

## 18. PWA, responsive behaviour, and offline

| ID | Requirement | Drivers |
|---|---|---|
| FSD-OFF-001 | The PWA MUST install from supported desktop/mobile browsers and launch a cached public shell with an explicit online/offline indicator. | PRD-PLAT-001 |
| FSD-OFF-002 | Authenticated content becomes offline-available only after explicit Pin or review-pack download. Ordinary authenticated responses are not generically cached. | PRD-PLAT-002 |
| FSD-OFF-003 | A pinned snapshot MUST show source/document revision time and stale status. Offline citations navigate only to locally available locators and identify unavailable assets. | PRD-PLAT-002 |
| FSD-OFF-004 | A seven-day review pack MUST show creation/expiry, included courses/items, storage use, and refresh action. Sealed answers/rubrics are not inspectable from storage. | PRD-PLAT-002 |
| FSD-OFF-005 | Offline actions are limited to shell navigation, pinned reading, and downloaded review responses. Ask, global search, import, sync, MCP, document editing, settings/security changes, and new test generation are disabled with explanation. | PRD-PLAT-002 |
| FSD-OFF-006 | Offline review submissions MUST remain visibly provisional and retryable until canonical server acknowledgement. Logout/account switch MUST clear the account's local namespace and key. | PRD-PLAT-002, PRD-PRIV-002 |
| FSD-OFF-007 | A service-worker update MUST not replace an active test or dirty editor. It displays Update ready and activates after safe completion/save. | PRD-PLAT-001 |
| FSD-OFF-008 | Browser storage eviction or quota denial MUST be reported; canonical online content remains unaffected and the user can unpin content. | PRD-OPS-002 |

### Responsive layout

- Desktop: persistent navigation, main content, and optional right inspector.
- Tablet: compact rail and inspector drawer.
- Phone: full-width route, bottom navigation/menu, inspector as full-height sheet,
  touch-safe controls, and horizontally scrollable tables.
- The editor may use a focused full-screen sheet for complex table/math/media
  controls on small screens.

## 19. Accessibility and language

| ID | Requirement | Drivers |
|---|---|---|
| FSD-A11Y-001 | Core v1 journeys MUST target WCAG 2.2 AA and be usable with keyboard alone. | PRD-PLAT-004 |
| FSD-A11Y-002 | Every input has a programmatic label, instruction/error association, visible focus, and logical tab order. Icon-only actions have accessible names. | PRD-PLAT-004 |
| FSD-A11Y-003 | Dynamic job, save, answer, sync, offline, and error states MUST announce concise changes through appropriate live regions without repeatedly interrupting. | PRD-PLAT-004 |
| FSD-A11Y-004 | Test confidence, correctness, evidence, recall, conflict, source quality, and private status MUST not rely on color alone. | PRD-PLAT-004 |
| FSD-A11Y-005 | Dialogs/sheets MUST trap and restore focus; destructive confirmations state affected scope. Reduced motion and zoom/reflow must remain usable. | PRD-PLAT-004 |
| FSD-A11Y-006 | Hindi/Devanagari and Hinglish text MUST preserve Unicode, direction, searchable exact terms, line wrapping, and readable fonts. UI chrome remains English in v1. | PRD-PLAT-003 |
| FSD-A11Y-007 | Source page regions, formulas, tables, code, citations, graph/tree relations, and editor blocks require meaningful screen-reader alternatives or structured navigation. | PRD-PLAT-004 |

## 20. Operational status behaviour

| ID | Requirement | Drivers |
|---|---|---|
| FSD-OPS-001 | The global status surface MUST aggregate active ingestion, sync, export, deletion, projection rebuild, and offline replay jobs without requiring the originating route to remain open. | PRD-OPS-001 |
| FSD-OPS-002 | Job detail MUST show stable job ID, accepted time, stage/attempt history, warnings, retryability, last update, and user-safe correlation ID. | PRD-OPS-001 |
| FSD-OPS-003 | Tex outage MUST preserve canonical writes, source/history browsing, exact/graph/local-semantic retrieval, export, deletion, and self-host use; context receipts show degraded Tex. | PRD-OPS-003 |
| FSD-OPS-004 | Model outage MUST return cited evidence/context when possible rather than fabricate an answer. Retry/provider options must respect disclosure policy. | PRD-OPS-003 |
| FSD-OPS-005 | Maintenance or global capacity protection MUST have a public status message and honest retry/queue behaviour; accepted work remains durable. | PRD-BETA-003 |
| FSD-OPS-006 | Beta/experimental labels MUST appear next to the affected capability rather than only in Terms or release notes. | PRD-BETA-004 |

## 21. Acceptance scenarios

These scenarios are normative examples. Detailed technical/property/security
coverage lives in the [Evaluation and Release Gates](../technical/EVALUATION_RELEASE_GATES.md).

| ID | Given | When | Then |
|---|---|---|---|
| FSD-AC-001 | A Google-authenticated new user | They confirm 18+ | The account activates and onboarding begins without payment/invite. |
| FSD-AC-002 | A Google-authenticated new user | They cannot confirm 18+ | No active content account is created; adults-only explanation is shown. |
| FSD-AC-003 | A Space marked Private | A connected AI calls any read/write tool | No item/existence signal from that Space is returned and writes targeting it fail indistinguishably. |
| FSD-AC-004 | A new non-private Space and an existing AI connection | The Space becomes eligible | Consent policy makes it part of the fixed whole-account grant; the user was warned before changing eligibility. |
| FSD-AC-005 | An uploaded source is accepted | The page refreshes or a worker restarts | The same durable job and stage remain visible without duplicate revision. |
| FSD-AC-006 | A scan has low-confidence pages | Parsing finishes | Source is Ready with warnings or deep-parse pending, with affected pages visible. |
| FSD-AC-007 | Two tabs share one document base | One saves before the other | The later save receives conflict options and cannot overwrite silently. |
| FSD-AC-008 | An AI patch references an older document revision | The user tries to approve | Proposal becomes Conflicted and requires review/rebase. |
| FSD-AC-009 | Account sources answer only part of a question | Ask completes | The answer cites supported claims and clearly labels missing/external knowledge. |
| FSD-AC-010 | Current official material conflicts with a student note | Ask compiles context | Both claims/revisions appear; retrieval rank does not silently resolve authority. |
| FSD-AC-011 | A learner reveals an answer or uses a substantive hint | The attempt is graded correct | It is practice-only and cannot establish demonstrated recall. |
| FSD-AC-012 | A written grade is low confidence | Results render | Grade is Provisional and no demonstrated-state change occurs. |
| FSD-AC-013 | A seven-day review pack is available offline | The learner responds | Attempt remains Pending sync until deduplicated server acknowledgement. |
| FSD-AC-014 | An external client proposes a fact | Tool succeeds | Memory → Proposed receives it; search/fetch cannot see it before approval. |
| FSD-AC-015 | A client supplies explicit raw turns | `record_interaction` succeeds | Turns, client, receipt, and completeness are retained; learning evidence is unchanged. |
| FSD-AC-016 | A client omits surrounding host turns | The user inspects capture | It is Partial/Single turn, never Complete. |
| FSD-AC-017 | An external AI grant is revoked | It makes another request | The request fails before retrieval; past disclosure remains in activity explanation. |
| FSD-AC-018 | A Notion source lies outside the Memdot root | Memdot syncs | Content imports as a new source revision; no remote write is attempted. |
| FSD-AC-019 | An approved Memdot document lies under the root | One side changes | The other side receives an idempotent version update. |
| FSD-AC-020 | Both Notion and Memdot change from one base | Sync runs | That item pauses and offers Keep Notion, Keep Memdot, or reviewed merge. |
| FSD-AC-021 | Tex times out | Ask/search runs | Safe OSS retrieval continues, privacy/version rules remain identical, and degradation is receipted. |
| FSD-AC-022 | An item deletion is confirmed | Any client immediately fetches it | It is unavailable while durable purge continues; restore cannot republish it. |
| FSD-AC-023 | Global capacity protection activates | New work arrives | It is durably queued or refused before acceptance with retry guidance; no fabricated success appears. |
| FSD-AC-024 | A self-host operator disables Tex and paid APIs | Acceptance suite runs | Core ingestion, local retrieval, Learning, MCP, export, and deletion remain functional. |

## 22. Traceability summary

| Functional domain | Product drivers | Technical owners | Decisions |
|---|---|---|---|
| Auth/onboarding/settings | PRD-PRIV-001..006, PRD-BETA-001 | TRD-SYS, TRD-SEC | ADR-0010, ADR-0011 |
| Navigation/Today | PRD-CORE-001..006, PRD-LEARN-001..007 | TRD-SYS, TRD-LRN | ADR-0001, ADR-0012 |
| Library/Spaces/Sources | PRD-CORE-001..006 | TRD-DATA, TRD-ING, TRD-RET | ADR-0001, ADR-0002, ADR-0004 |
| Rich documents | PRD-CORE-004, PRD-AI-003 | TRD-DOC | ADR-0009 |
| Ingestion/processing | PRD-CORE-002..005, PRD-OPS-001..004 | TRD-ING, TRD-OPS | ADR-0002, ADR-0004 |
| Ask/search/context | PRD-AI-001..005, PRD-LEARN-002 | TRD-RET | ADR-0003, ADR-0005, ADR-0006 |
| Test/Review/Evidence Twin | PRD-LEARN-001..007 | TRD-LRN | ADR-0012 |
| Memory/proposals/capture | PRD-CORE-006, PRD-AI-003, PRD-INT-002..004 | TRD-DATA, TRD-MCP | ADR-0007, ADR-0008 |
| Notion | PRD-INT-005 | TRD-NOT | ADR-0014 |
| External AI | PRD-INT-001..004, PRD-PRIV-002 | TRD-MCP, TRD-API, TRD-SEC | ADR-0006, ADR-0007, ADR-0008 |
| Export/deletion | PRD-PRIV-003..004 | TRD-SEC, TRD-OPS | ADR-0002, ADR-0003 |
| PWA/offline/accessibility | PRD-PLAT-001..004 | TRD-SYS, TRD-SEC | ADR-0009, ADR-0013 |
| Beta safety/degradation | PRD-BETA-001..004, PRD-OPS-001..004 | TRD-API, TRD-OPS | ADR-0003, ADR-0011 |

## 23. Explicit v1 exclusions

V1 does not include payment/billing, advertised monthly quotas, institutions,
teams/collaboration, minors, native mobile apps, arbitrary browser-extension chat
capture, databases/board views in the editor, general offline editing, global
force-directed graph, arbitrary URL crawling, audio/video ingestion, Google
Drive, Calendar/Tasks, page-level PDF editing, high-stakes proctoring, or
automatic promotion of model/world knowledge to source truth.
