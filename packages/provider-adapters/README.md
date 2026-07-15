# Provider adapters

Concrete retrieval/model/object-store adapters live here and depend inward on
`packages/domain-python` ports. Domain policy must never import this package.
Phase 1 includes a health-only stub adapter for boundary enforcement only.
