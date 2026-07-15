#!/usr/bin/env bash
set -euo pipefail

# Phase 1: Compose topology is deferred to Phase 2.
# Validate only that ownership placeholders exist.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test -f "$ROOT/infra/compose/README.md"
test -f "$ROOT/infra/hosted/README.md"
echo "Compose validation: N/A until Phase 2 (placeholders present)."
