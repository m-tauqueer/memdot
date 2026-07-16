#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROJECT="${COMPOSE_PROJECT_NAME:-memdot}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
COMPOSE=(docker compose --project-name "$PROJECT" --env-file "${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}" "${FILES[@]}")
ID="ops-$(date -u +%Y%m%dT%H%M%SZ)"
PAYLOAD="fixture-$(openssl rand -hex 8)"
CHECKSUM="$(printf '%s' "$PAYLOAD" | sha256sum | awk '{print $1}')"

"${COMPOSE[@]}" exec -T postgres \
  psql -U memdot -d memdot_ops -v ON_ERROR_STOP=1 \
  -c "INSERT INTO ops_durability_fixture(id, payload, checksum) VALUES ('$ID', '$PAYLOAD', '$CHECKSUM');"

"${COMPOSE[@]}" restart postgres
for _ in $(seq 1 60); do
  status="$("${COMPOSE[@]}" ps postgres --format '{{.Status}}' || true)"
  if echo "$status" | grep -q healthy; then
    break
  fi
  sleep 2
done

ROW="$("${COMPOSE[@]}" exec -T postgres \
  psql -U memdot -d memdot_ops -At -c "SELECT checksum FROM ops_durability_fixture WHERE id='$ID';")"
if [[ "$ROW" != "$CHECKSUM" ]]; then
  echo "postgres fixture mismatch after restart" >&2
  exit 1
fi

"${COMPOSE[@]}" exec -T postgres \
  psql -U memdot -d memdot_ops -c "DELETE FROM ops_durability_fixture WHERE id='$ID';" >/dev/null
echo "postgres_durability_ok checksum=$CHECKSUM"
