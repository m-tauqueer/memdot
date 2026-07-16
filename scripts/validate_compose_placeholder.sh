#!/usr/bin/env bash
set -euo pipefail

# Phase 2: validate Compose topology policy (Tex absent, digests, exposure).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test -f "$ROOT/infra/compose/README.md"
test -f "$ROOT/infra/hosted/README.md"
test -f "$ROOT/infra/compose/compose.yaml"
test -f "$ROOT/infra/compose/images.lock.yaml"

uv run python "$ROOT/infra/compose/scripts/validate_compose_policy.py"
