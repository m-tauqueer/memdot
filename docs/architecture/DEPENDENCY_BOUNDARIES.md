# Dependency boundaries

This document is the Phase 1 ownership and dependency contract. Automated
checks enforce these rules; documentation alone is not sufficient.

## Allowed direction

```text
apps/web  ──► packages/contracts ──► (generated from) services/core OpenAPI
apps/mcp  ──► packages/contracts ──► services/core (HTTP only)

services/core          ──► packages/domain-python
services/workers       ──► packages/domain-python
services/model-router  ──► packages/domain-python

packages/domain-python          ──► provider ports (interfaces only)
packages/provider-adapters      ──► packages/domain-python (implements ports)

apps/web ──► packages/ui
```

Provider adapters live in `packages/provider-adapters`, never inside
`packages/domain-python`. Domain policy must not import adapters.

## Forbidden

| From                     | Must not import / query                                                                   |
| ------------------------ | ----------------------------------------------------------------------------------------- |
| `apps/web`, `apps/mcp`   | PostgreSQL drivers, object-storage SDKs, Tex SDKs, model-provider SDKs, provider adapters |
| `apps/mcp`               | `services/core` Python internals or filesystem packages                                   |
| `services/workers`       | `packages/ui`, `apps/web`, sibling Python services                                        |
| `services/core`          | sibling services, `packages/provider-adapters`                                            |
| `packages/domain-python` | Concrete provider adapters (`memdot_provider_adapters`)                                   |
| TypeScript packages      | Reimplementation of Python domain policy                                                  |

## Enforcement

- TypeScript: ESLint `no-restricted-imports` plus `dependency-cruiser`.
- Python: `import-linter` contracts in root `pyproject.toml`:
  - domain must not import services or provider adapters;
  - core/workers/model-router are mutually independent;
  - provider adapters may depend on domain only;
  - core must not import provider adapters.
- CI fails on boundary violations and on deliberately failing fixture suites that
  do not fail.

## Phase 1 note

Skeletons expose health/readiness and contract tooling only. Full Compose,
database, and provider wiring belong to later phases.
