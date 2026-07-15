# Evaluation and Release Gates

Status: **Founding specification**
Date: **2026-07-15**

## 1. Principle

Memdot has no single "RAG score." Parser fidelity, retrieval, citation,
version/conflict behaviour, context selection, learner evidence, security,
offline replay, and degraded operation have independent hard gates. Strong
averages cannot hide a stale-current answer, bad locator, private-space leak, or
invalid learning-state update.

The product north star is **source-grounded delayed success on novel assessment
items**. Chat volume, time spent, streaks, and generated-card counts are not
substitutes.

## 2. Benchmark package

Create a versioned `Memdot Memory Benchmark` with:

```text
corpus.jsonl          sources, immutable revisions, authority and effective time
elements.jsonl        gold tree, text, tables, formulas and locators
tasks.jsonl           query, intent, scope, as_of, grants and budget
qrels.jsonl           graded relevance judgements
graph_gold.jsonl      curriculum nodes, edges and source anchors
security_vectors.json privacy, injection, OAuth/MCP and enumeration cases
```

Target beta corpus:

- 16 synthetic or openly licensed course packs and about 1,600 pages.
- 1,000 judged retrieval/context tasks.
- STEM, computer science, economics, history, literature, and exam preparation.
- Approximately 60% English, 20% Hindi, and 20% Hinglish/code-mixed material.
- Born-digital/scanned PDF, image, DOCX, PPTX, Markdown, text, paste, rich
  MemdotDocument, and Notion fixtures.
- Two or three revisions per course pack with amendments, retractions,
  conflicting authority, and distractors.
- A separate handwriting challenge slice that does not block v1.

Tasks are split by whole source/course family, never random chunks. Two trained
annotators independently label graded relevance, conflict, graph relations, and
citation support; freeze a slice only when inter-annotator agreement is at least
0.80. Models may propose tasks, but humans verify all hidden-test labels.

Use [RAGChecker](https://github.com/amazon-science/RAGChecker) for diagnostic
claim metrics, [ALCE](https://github.com/princeton-nlp/ALCE) for citation
methodology, [TREC](https://trec.nist.gov/howto.html) pooling for relevance
judgements, and [OmniDocBench](https://github.com/opendatalab/OmniDocBench) as an
external parser sanity check. Automated judges never replace deterministic
checks or human-calibrated release decisions.

## 3. Ingestion and parser gates

| ID | Gate | Required result |
|---|---|---|
| EVAL-ING-001 | Determinism | Same bytes and parse profile produce identical revision, element, and chunk IDs in 100% of reruns. |
| EVAL-ING-002 | Completeness | No failed or omitted page is reported as successful. |
| EVAL-ING-003 | Provenance | Every promoted element has a valid source revision and page/block/line locator. |
| EVAL-ING-004 | Born-digital text | Character accuracy at least 99.5%. |
| EVAL-ING-005 | Printed English OCR | Character accuracy at least 98%. |
| EVAL-ING-006 | Printed Hindi OCR | Character accuracy at least 95%. |
| EVAL-ING-007 | Structure | Block-type macro F1 at least 0.95 born-digital and 0.90 printed scans. |
| EVAL-ING-008 | Reading order | Pairwise accuracy at least 0.98 born-digital and 0.95 scans. |
| EVAL-ING-009 | Tables | TEDS at least 0.95 born-digital and 0.85 scans. |
| EVAL-ING-010 | Formula | Structural exact match at least 0.95 born-digital and 0.80 scans. |
| EVAL-ING-011 | Locator open | Correct click-to-source region at least 99.5% born-digital and 97% scans. |
| EVAL-ING-012 | Retry | Workflow replay creates no duplicate canonical records. |

Low-confidence pages must be visible or routed to the deep parser. Parser/model
upgrades run as shadow parse profiles and cannot replace the active profile until
the complete slice comparison passes.

## 4. Retrieval gates

Report source- and element-level Recall@5/10/20, nDCG@10, MRR@10, all-required
multi-hop recall, exact-token/formula hits, stale evidence, and wrong-course or
wrong-edition contamination.

| ID | Gate | Required result |
|---|---|---|
| EVAL-RET-001 | Overall Recall@20 | At least 0.90. |
| EVAL-RET-002 | Overall nDCG@10 | At least 0.80. |
| EVAL-RET-003 | Exact identifier/formula Hit@5 | At least 0.98. |
| EVAL-RET-004 | Candidate Recall@50 | At least 0.95 for the local hybrid lane. |
| EVAL-RET-005 | Multi-hop joint recall | At least 0.85. |
| EVAL-RET-006 | Current revision | Zero superseded/retracted evidence in default-current context. |
| EVAL-RET-007 | Critical slices | No language/format/intent slice regresses by more than three absolute nDCG points. |

Exact cases include course codes, theorem names, chemical formulae, quoted
phrases, code identifiers, Devanagari numerals, OCR noise, Romanised Hindi, and
equivalent LaTeX/rendered formula forms. Evaluate lexical-only, dense-only,
hybrid, and hybrid-plus-reranker with identical chunking and filters.

## 5. Version, history, and conflict gates

- Deterministic planted current/historical filters: 100% correct revision.
- Retracted facts presented as current: zero.
- Historical `as_of` answer accuracy: at least 95%.
- Conflict behaviour precision/recall: at least 95%.
- Change-summary coverage of required amendments: at least 95%.
- Learner misconception promoted into canonical source truth: zero.
- Unresolved disagreement must be exposed, scoped, or answered under an explicit
  authority rule; never silently averaged.

## 6. Curriculum and learner-state gates

| ID | Gate | Required result |
|---|---|---|
| EVAL-LRN-001 | Curriculum node F1 | At least 0.90. |
| EVAL-LRN-002 | Edge precision/recall | At least 0.95 / 0.85. |
| EVAL-LRN-003 | Source anchoring | 100% of promoted nodes and relations. |
| EVAL-LRN-004 | Confirmed prerequisite graph | Zero cycles. |
| EVAL-LRN-005 | Suggested edges | Never block progression or establish confirmed truth. |
| EVAL-LRN-006 | Event replay | Exactly deterministic under duplicates and out-of-order delivery. |
| EVAL-LRN-007 | Evidence eligibility | No revealed, substantively hinted, post-feedback, or ungradable event raises demonstrated status. |
| EVAL-LRN-008 | Sealed answers | Zero answer-key exposure before submission. |

Property-test no-hint/minor-hint/substantive-hint, response-before/after reveal,
same-item retry, user-marked conversation, retired source/item, offline event
replay, and deletion/rebuild sequences.

## 7. Context and answer gates

### Compiled context

- Required-evidence coverage at least 95%.
- Context precision at least 75%.
- Provenance coverage and token/character-budget compliance 100%.
- Duplicate-token ratio at most 5%.
- Material conflict detection at least 95%.
- Deleted, private, cross-account, wrong-edition, or unauthorised elements: zero.
- Every included item appears in the receipt with revision, locator, selection
  reason, route, and user-openable URL.

Shuffle candidate order, double distractors, insert near-duplicates, move
required evidence through the context, and add malicious instructions inside
sources. Benign noise may reduce evidence/citation success by at most three
points; content instructions may never alter system policy or permissions.

### Generated answers

- Overall answer correctness at least 90%.
- Claim faithfulness and citation correctness at least 98%.
- Citation completeness at least 95%.
- Locator correctness at least 99%.
- Unsupported factual claims at most 1%.
- Correct abstention or clarification at least 95%.

Freeze judge model, prompt, and version. Run open-ended cases three times and
publish variance. Human-review a stratified 10% sample; automated judgement is
not release-authoritative until agreement with humans reaches 0.75.

## 8. Tex and OSS parity

Run the frozen suite in four modes:

1. PostgreSQL exact/version/graph plus Tex semantic retrieval.
2. Tex-only diagnostic lane.
3. Tex unavailable: PostgreSQL FTS/trigram/graph plus pgvector/local reranking.
4. Tex recovery and complete rebuild from canonical state.

Authorization, private-space exclusion, revision rules, deletion, public IDs,
citation locators, learner projection, MCP schemas, and receipt format must be
identical in every mode. Ranking need not be identical.

The fallback must independently meet exact Hit@5 of 0.98, expose zero stale or
unauthorised evidence, retain at least 85% of primary Recall@20, keep end-to-end
answer correctness within five points of primary, and have no citation-correctness
regression. The receipt identifies degraded retrieval.

Inject Tex timeouts, 429/500 responses, delayed jobs, duplicate callbacks,
partial batches, failed deletion, out-of-order revisions, and prolonged outage.
Canonical reads must remain correct; replay must converge without duplication.

## 9. MCP and REST gates

- `search({query})` and `fetch({id})` exact input compatibility.
- Output-schema validation and identical `structuredContent`/JSON text payloads.
- Absolute user-openable citation URLs and search-to-fetch referential integrity.
- Stable IDs, signed pagination cursors, idempotent writes, and deletion behaviour.
- OAuth issuer/JWKS/audience/resource/scope/expiry checks.
- Wrong-audience, replayed, downgraded, revoked, and enumerated-token cases.
- `propose_memory` creates only pending proposals.
- `record_interaction` records capture completeness and never changes learner
  evidence without a later user action.
- Compatibility runs against ChatGPT, Claude remote MCP, and Gemini CLI.
- Consumer Gemini is not a v1 compatibility claim unless available and tested in
  India at release time.

Validation, auth, privacy, and side-effect gates require 100% pass. Any data
exposure is a release blocker.

## 10. Editor, Notion, and PWA gates

- `MemdotDocument v1 -> editor -> v1` exact round-trip fixtures.
- Stable/new block IDs across split, merge, paste, duplicate, and import.
- Schema migration idempotence and unknown-node preservation.
- Two-tab stale-base conflicts; no silent last-writer-wins.
- AI patch proposal base drift and source-citation validation.
- XSS corpus for paste, links, SVG, KaTeX, code, assets, and embeds.
- Notion nested pagination, expiring-asset copy, unsupported-block preservation,
  write-area boundary, idempotency, and concurrent-change conflict.
- Offline cold launch, account isolation, logout purge, quota eviction, stale
  badge, update-with-dirty-editor, provisional attempt replay, and server
  reconciliation.
- Installed iOS/Android PWA smoke checks plus Playwright Chromium/WebKit/Firefox,
  keyboard, screen-reader, touch, and responsive-table tests.

## 11. Performance, resilience, and beta safety

| ID | SLO/gate | Target |
|---|---|---|
| EVAL-OPS-001 | MCP search p95 | <= 1.5 seconds |
| EVAL-OPS-002 | MCP fetch p95 | <= 500 ms |
| EVAL-OPS-003 | Context compilation p95 | <= 3 seconds excluding generation |
| EVAL-OPS-004 | Successful tool calls | >= 99.5% excluding valid client errors |
| EVAL-OPS-005 | Ingestion durability | No accepted upload lost under worker/process restart |
| EVAL-OPS-006 | Recovery | RPO <= 15 minutes; RTO <= 4 hours |

The unlimited beta has no monthly user quota, but tests must prove that oversized
files, excessive concurrency, provider-budget exhaustion, and queue overload
produce documented rejection, queued, or degraded states without data loss,
priority inversion, cross-account impact, or unbounded spend.

## 12. Cadence and promotion

- Every PR: schemas/contracts, deterministic parser fixtures, property/privacy
  tests, and a 100-task retrieval smoke set.
- Nightly: full 1,000-task primary/fallback benchmark.
- Release candidate: three generative runs, failure injection, supported MCP
  clients, restore/deletion drill, and human citation audit.
- Weekly beta: at least 50 opt-in/redacted hard-case reviews.

A candidate promotes only when every hard invariant passes, every critical slice
meets its absolute threshold, paired bootstrap 95% intervals show no material
non-inferiority loss, and the complete run is reproducible from corpus, source,
configuration, parser/index/model, output, and judge hashes. Any cross-account
leak, private-space leak, invalid-current citation, sealed-key leak, deleted-data
resurrection, or learner-state corruption triggers rollback rather than A/B
evaluation.

## 13. Traceability

This document is the verification owner for the following frozen requirement
families. Individual test cases MUST record the exact requirement IDs they
cover, their fixture/corpus version, and their result artifact.

| Gate area | Product and functional requirements | Technical contracts | Primary decisions |
|---|---|---|---|
| Parsing, versions, and conflicts | PRD-CORE-002..005; FSD-SRC-*; FSD-ING-* | TRD-DATA-*; TRD-DOC-*; TRD-ING-* | ADR-0002, ADR-0004 |
| Retrieval, context, and answers | PRD-CORE-003..005; PRD-AI-001..004; FSD-ASK-* | TRD-RET-* | ADR-0003, ADR-0005, ADR-0006 |
| Learning evidence and review | PRD-LEARN-001..007; FSD-TST-*; FSD-REV-* | TRD-LRN-* | ADR-0012 |
| MCP, consent, and private-space isolation | PRD-INT-001..004; PRD-PRIV-002; FSD-INT-* | TRD-MCP-*; TRD-API-*; TRD-SEC-* | ADR-0007, ADR-0008 |
| Editor, Notion, and offline PWA | PRD-CORE-004; PRD-INT-005; PRD-PLAT-001..004; FSD-DOC-*; FSD-NOT-*; FSD-OFF-* | TRD-DOC-*; TRD-NOT-*; TRD-SYS-* | ADR-0009, ADR-0013, ADR-0014 |
| Resilience, deletion, and self-host parity | PRD-PRIV-003..006; PRD-PLAT-005..006; PRD-BETA-001..004; PRD-OPS-001..004; FSD-EXP-*; FSD-OPS-* | TRD-DEP-*; TRD-OPS-*; TRD-SEC-* | ADR-0003, ADR-0010, ADR-0011 |
