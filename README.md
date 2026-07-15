# Memdot

Memdot is a general memory platform with Learning as its first flagship mode.
This repository contains the founding specification and a Phase 1 monorepo
scaffold. Product behavior is not implemented yet.

## Status

**Phase 1 candidate scaffold** — repository foundation, service/package
skeletons, contract-generation toolchain, and CI hygiene. No domain product
features, database ledger, authentication, ingestion, retrieval, Learning, MCP
tools, Notion, or Compose topology are claimed as complete.

Owner decisions, commits, and phase transitions remain with Tauqueer. Codex
audits each macro-phase before an accepted commit.

## Start here

| Document                                               | Purpose                                       |
| ------------------------------------------------------ | --------------------------------------------- |
| [CONTEXT.md](CONTEXT.md)                               | Verified current state and durable invariants |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)       | Phase order and deliverables                  |
| [IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md) | Detailed micro-phase checklist                |
| [AGENTS.md](AGENTS.md)                                 | Agent operating rules and verified commands   |
| [docs/README.md](docs/README.md)                       | Documentation index                           |

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
