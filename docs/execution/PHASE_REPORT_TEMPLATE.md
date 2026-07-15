# Grok Phase Report Template

Use this once, at the end of a complete macro-phase. Do not submit routine
reports between micro-phases.

## GROK PHASE REPORT — PHASE X

### 1. Repository state

- Phase:
- Branch:
- Base commit:
- Current HEAD:
- Pre-existing changes:
- git status --short:

### 2. Completed scope

- Macro-phase objective:
- Completed micro-phases:
- Explicit non-goals:
- Deviations from the implementation plan:

### 3. Traceability

- PRD requirements:
- FSD requirements and acceptance scenarios:
- TRD requirements:
- ADRs:
- Threat-model controls:
- Evaluation gates:

### 4. Micro-phase self-checks

For every micro-phase:

- Micro-phase ID and name:
- Logic implemented:
- Files changed:
- Validation commands:
- Raw result summary:
- Failures found and fixed:
- Remaining limitation:

### 5. Changed-file inventory

Group every created, modified, generated, renamed, and deleted file by:

- repository/tooling;
- application/service;
- package/contract;
- infrastructure;
- test/fixture;
- documentation;
- generated artifact.

### 6. Data and compatibility impact

- Database migrations and heads:
- RLS/policy changes:
- OpenAPI changes:
- JSON Schema changes:
- Event versions:
- Generated-client changes:
- Configuration/environment changes:
- Backward-compatibility effect:
- Export/deletion effect:

### 7. Validation evidence

For every command provide the exact command, exit code, and unedited relevant
terminal output:

- clean bootstrap/install;
- formatting/lint;
- Python typing;
- TypeScript typing;
- unit tests;
- property tests;
- contract/schema tests;
- integration tests;
- security/privacy tests;
- documentation links/Mermaid;
- container builds and health;
- phase-specific benchmarks;
- git diff --check.

Also report:

- tests passed:
- tests failed:
- tests skipped and exact reason:
- expected failures:
- coverage:
- benchmark/corpus/profile hashes:
- performance measurements:
- flaky reruns:

### 8. Phase exit gate

Copy every Phase X exit-gate item from IMPLEMENTATION_TRACKER.md and mark it
PASS, FAIL, or BLOCKED with evidence.

### 9. Security and privacy

- Account/RLS impact:
- Private-Space impact:
- Secrets/credentials impact:
- Provider egress:
- Telemetry/logging:
- Proposal/canonical-write impact:
- Learner-evidence impact:
- Export/deletion/restore impact:
- New threat or mitigation:

### 10. Diff evidence

Include:

- git status --short;
- git diff --stat;
- git diff --check;
- complete reviewable diff or patch;
- generated files;
- migration files;
- lockfiles;
- any binary/artifact inventory.

### 11. Known limitations and blockers

- Known limitations:
- Deferred work that belongs to later phases:
- Unresolved blocker:
- Owner decision required:

### 12. Authority confirmation

- No unauthorized commit:
- No unauthorized push or merge:
- No unauthorized deployment:
- No unauthorized credential rotation:
- No unauthorized paid/external resource creation:
- No unauthorized production or third-party data mutation:

### 13. Requested Codex action

Audit the complete phase and return exactly one:

- PASS
- FAIL — CORRECTIONS REQUIRED
- BLOCKED — OWNER DECISION REQUIRED
