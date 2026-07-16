# Memdot

Memdot is a general memory platform with Learning as its first flagship mode.
This repository contains the founding specification and the accepted backend
foundation through technical Phase 3.

## Status

**Technical Phases 1–3 accepted** — deterministic monorepo, Tex-disabled
self-host platform, canonical PostgreSQL ledger foundations, tenancy, FORCE RLS,
and OIDC/session authentication. Wave 4 (technical Phases 4–5: Core runtime and
ingestion) is next but not owner-authorized.

Owner decisions, commits, and wave transitions remain with Tauqueer. Codex
audits each delivery wave before an accepted commit.

## Start here

| Document                                               | Purpose                                        |
| ------------------------------------------------------ | ---------------------------------------------- |
| [CONTEXT.md](CONTEXT.md)                               | Verified current state and durable invariants  |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)       | Delivery waves, smoke policy, and deliverables |
| [IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md) | Detailed wave and micro-phase checklist        |
| [AGENTS.md](AGENTS.md)                                 | Agent operating rules and verified commands    |
| [docs/README.md](docs/README.md)                       | Documentation index                            |

Architecture ownership and dependency direction:
[docs/architecture/DEPENDENCY_BOUNDARIES.md](docs/architecture/DEPENDENCY_BOUNDARIES.md).

## Verified Phase 1 commands

These commands were exercised during Phase 1 scaffolding. Prefer them over
invented alternatives.

```bash
make bootstrap      # install TypeScript (pnpm) and Python (uv) deps with frozen lockfiles
make format         # format TypeScript and Python
make lint           # lint TypeScript and Python
make typecheck      # TypeScript and Python type checks
make test           # unit tests
make contracts      # regenerate and validate contracts
make docs-validate  # documentation links and Mermaid parse
make build          # build all skeletons
make containers     # build runtime Docker images + non-root checks
make container-smoke # health-endpoint smoke against running images
make check          # full local CI-equivalent suite
make clean          # remove local build/cache artifacts
```

See [AGENTS.md](AGENTS.md) and [docs/ai/CODEBASE_CONTEXT_MAP.md](docs/ai/CODEBASE_CONTEXT_MAP.md)
for the authoritative verified command list.

## License

Apache License 2.0. See [LICENSE](LICENSE) and ADR-0011.
