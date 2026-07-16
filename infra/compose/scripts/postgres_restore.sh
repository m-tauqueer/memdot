#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROJECT="${COMPOSE_PROJECT_NAME:-memdot}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
COMPOSE=(docker compose --project-name "$PROJECT" --env-file "${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}" "${FILES[@]}")
DUMP="${1:?usage: postgres_restore.sh <dump-file> <target_db>}"
TARGET_DB="${2:?usage: postgres_restore.sh <dump-file> <target_db>}"

TIMEOUT_SEC="${POSTGRES_RESTORE_TIMEOUT_SEC:-120}"

if [[ ! "$TARGET_DB" =~ ^memdot_restore_[a-z0-9_-]+$ ]]; then
  echo "refusing restore into non-disposable database: $TARGET_DB" >&2
  echo "allowed pattern: memdot_restore_<unique-id>" >&2
  exit 2
fi

if [[ ! -f "$DUMP" ]]; then
  echo "dump not found: $DUMP" >&2
  exit 2
fi

if [[ -f "${DUMP}.sha256" ]]; then
  expected="$(tr -d '[:space:]' <"${DUMP}.sha256")"
  actual="$(sha256sum "$DUMP" | awk '{print $1}')"
  if [[ "$expected" != "$actual" ]]; then
    echo "checksum mismatch; refusing restore" >&2
    exit 3
  fi
else
  echo "missing checksum sidecar ${DUMP}.sha256; refusing restore" >&2
  exit 3
fi

PG_ID="$("${COMPOSE[@]}" ps -q postgres)"
docker cp "$DUMP" "$PG_ID:/tmp/restore.dump"

if ! timeout "$TIMEOUT_SEC" "${COMPOSE[@]}" exec -T postgres pg_restore -l /tmp/restore.dump >/dev/null; then
  echo "corrupt dump; refusing restore" >&2
  exit 3
fi

"${COMPOSE[@]}" exec -T postgres \
  psql -U memdot -d postgres -v ON_ERROR_STOP=1 \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$TARGET_DB' AND pid <> pg_backend_pid();" \
  >/dev/null 2>&1 || true
"${COMPOSE[@]}" exec -T postgres \
  psql -U memdot -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS \"$TARGET_DB\";" \
  -c "CREATE DATABASE \"$TARGET_DB\" OWNER memdot;"

timeout "$TIMEOUT_SEC" "${COMPOSE[@]}" exec -T postgres \
  pg_restore -U memdot -d "$TARGET_DB" --no-owner --no-acl /tmp/restore.dump

echo "restore_ok target=$TARGET_DB"
