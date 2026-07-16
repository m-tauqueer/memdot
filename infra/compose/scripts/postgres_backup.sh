#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROJECT="${COMPOSE_PROJECT_NAME:-memdot}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
COMPOSE=(docker compose --project-name "$PROJECT" --env-file "${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}" "${FILES[@]}")
OUT_DIR="${1:-$ROOT/infra/compose/.backup}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT_DIR"
TARGET="$OUT_DIR/memdot_ops_${STAMP}.dump"

"${COMPOSE[@]}" exec -T postgres \
  pg_dump -U memdot -d memdot_ops -Fc --no-owner --no-acl >"$TARGET"

sha256sum "$TARGET" | awk '{print $1}' >"${TARGET}.sha256"
echo "backup=$TARGET"
echo "checksum=$(cat "${TARGET}.sha256")"
