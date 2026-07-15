# Ownership map

This file records architecture ownership for Memdot. It intentionally does **not**
invent GitHub usernames or CODEOWNERS identities. Product ownership remains with
Tauqueer.

| Path                         | Owns                                                 | Must not own                                                              |
| ---------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------- |
| `apps/web`                   | Next.js PWA shell, presentation, accessibility       | Authorization truth, provider adapters, direct DB/object/Tex/model access |
| `apps/mcp`                   | MCP/OAuth protocol edge, tool envelopes              | Canonical storage, retrieval, provider SDKs, Core internals               |
| `services/core`              | Canonical domain API, OpenAPI owner, public REST     | Binary parsing, long model calls, UI modules                              |
| `services/workers`           | Durable job execution skeletons                      | User-session authorization inventing, UI imports                          |
| `services/model-router`      | Isolated model-provider egress boundary              | Authorization, revision truth, learner evidence                           |
| `packages/contracts`         | Generated OpenAPI/JSON Schema/event artifacts        | Hand-written competing domain DTOs                                        |
| `packages/domain-python`     | Domain types and inward-facing provider ports        | Provider adapter implementations, UI                                      |
| `packages/provider-adapters` | Concrete provider adapters depending inward on ports | Authorization, revision truth, learner evidence, UI                       |
| `packages/ui`                | Accessible frontend primitives                       | Domain policy, backend imports                                            |
| `infra/compose`              | Self-host Compose topology (Phase 2+)                | Application domain logic                                                  |
| `infra/hosted`               | Hosted GCP definitions (later phases)                | Local developer secrets                                                   |
| `tests/benchmark`            | Frozen evaluation corpora and runners                | Production credentials                                                    |
| `tests/security`             | Cross-account and privacy adversarial suites         | Product feature implementation                                            |
| `docs/`                      | Product/technical/ADR/evaluation source of truth     | Unverified "implemented" claims                                           |
| `scripts/`                   | Verified repository automation                       | Domain policy                                                             |

## Dependency direction

See [docs/architecture/DEPENDENCY_BOUNDARIES.md](docs/architecture/DEPENDENCY_BOUNDARIES.md).

Allowed summary: `edge/UI -> Core APIs + generated contracts -> domain -> provider ports`;
adapters depend inward. Provider adapters never own authorization, revision
truth, public IDs, deletion truth, proposals, or learner evidence.
