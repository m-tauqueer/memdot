# ADR 0011: Apache-2.0 and Self-Host Parity

- Status: Accepted
- Date: 2026-07-15

## Context

Memdot should be trustworthy infrastructure for personal knowledge and learning, not a hosted-service trap. Users and institutions need to inspect, run, modify, and migrate the complete product while the hosted service remains sustainable through convenience and operations.

## Decision

- Memdot's product code is released under the Apache License 2.0. Third-party assets and dependencies retain their own compatible licenses.
- Self-hosted deployments have product-feature parity with hosted Memdot. Core ingestion, retrieval, Tex integration, tutoring, Learning, MCP, sync, export, and administration are not withheld as an open-core tier.
- Hosted differentiation is operational: managed regional infrastructure, upgrades, backups, monitoring, support, and included model usage.
- Cloud services sit behind documented interfaces for PostgreSQL, S3-compatible object storage, OIDC, key management, model providers, queues, and telemetry.
- A supported container-based deployment and upgrade/migration tooling are release requirements. Hosted and self-hosted builds use the same application code paths.
- Telemetry is off by default for self-hosting and content-free/declared when enabled.
- The software license does not grant Memdot trademarks or hosted-service identity; trademark guidance is maintained separately.

## Alternatives

- Proprietary hosted-only product: rejected because it undermines user control and long-term memory portability.
- Open core with private learning or MCP features: rejected because it creates architectural divergence and weakens trust.
- AGPL: rejected for the initial plan because Apache-2.0 better supports broad adoption and integration; sustainability relies on hosted operations, not reciprocity enforcement.

## Consequences

- Competitors may legally reuse the code under the license terms.
- Every managed dependency needs a self-hostable adapter or documented equivalent.
- Deployment quality, support, and reliable managed AI become the hosted product's value.

## Security effect

Self-host operators control residency, processors, credentials, backups, and retention and are responsible for their deployment. Defaults remain secure: no bundled production secrets, no public storage, telemetry off, and documented hardening and deletion procedures.

## Reversal strategy

Already released Apache-2.0 versions cannot be revoked. Future licensing changes would require a prospective ADR, contributor-rights review, and clear separation from existing releases; product data remains exportable regardless.

## Links

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [ADR 0002: PostgreSQL Evidence Ledger](0002-postgres-evidence-ledger.md)
- [ADR 0010: India-regional inference and direct adapters](0010-india-regional-inference-and-direct-adapters.md)
