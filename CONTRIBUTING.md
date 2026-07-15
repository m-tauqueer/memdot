# Contributing to Memdot

## Roles

- **Tauqueer** owns product decisions, commits, pushes, merges, deploys,
  credentials, paid resources, and phase transitions.
- **Grok** implements one owner-approved macro-phase, self-validates every
  micro-phase, and submits one consolidated phase report.
- **Codex** audits the complete phase diff and evidence, then returns PASS,
  FAIL — CORRECTIONS REQUIRED, or BLOCKED — OWNER DECISION REQUIRED.

Do not commit, push, merge, or deploy without Tauqueer's explicit authorization,
even after tests pass.

## Branch and change rules

1. Work only in the active owner-approved macro-phase.
2. Keep diffs scoped to the micro-phase. Do not sneak in later-phase product
   behavior.
3. Preserve founding documentation unless the phase explicitly requires updates.
4. Update AGENTS.md, CONTEXT.md, and the Codebase Context Map in the same change
   that introduces verified paths or commands.
5. Never invent GitHub identities in CODEOWNERS. Use [OWNERS.md](OWNERS.md) for
   architecture ownership until real GitHub handles exist.

## Tests and documentation

- Add or update tests with the behavior they cover.
- Prefer content-safe synthetic fixtures. Never commit secrets or personal data.
- Generated contracts must be regenerated from Core OpenAPI / schema owners;
  do not hand-edit competing DTOs.
- Documentation local links and Mermaid diagrams must remain valid.
- Failures on focused tests, unexplained skips, stale generated files, or
  dependency-boundary violations are blockers.

## Phase workflow

1. Tauqueer starts a macro-phase.
2. Grok completes every micro-phase in order, self-checking between them.
3. Grok runs the phase exit gate and produces one report from
   `docs/execution/PHASE_REPORT_TEMPLATE.md`.
4. Codex audits the complete phase.
5. Only a Codex PASS makes the phase eligible for an owner-authorized commit.

## Tooling

Use the verified root commands in the repository README and AGENTS.md. Inspect
manifests and CI before inventing new commands.
