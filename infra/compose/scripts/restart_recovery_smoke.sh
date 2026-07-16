#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROJECT="${COMPOSE_PROJECT_NAME:-memdot}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
COMPOSE=(docker compose --project-name "$PROJECT" --env-file "${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}" "${FILES[@]}")

ID="restart-$(date -u +%Y%m%dT%H%M%SZ)"
PAYLOAD="fixture-$ID"
CHECKSUM="$(printf '%s' "$PAYLOAD" | sha256sum | awk '{print $1}')"

"${COMPOSE[@]}" exec -T postgres \
  psql -U memdot -d memdot_ops -v ON_ERROR_STOP=1 \
  -c "INSERT INTO ops_durability_fixture(id, payload, checksum) VALUES ('$ID', '$PAYLOAD', '$CHECKSUM');"

for svc in postgres seaweedfs hatchet-engine workers openbao; do
  echo "restarting $svc"
  "${COMPOSE[@]}" restart "$svc"
  for _ in $(seq 1 90); do
    status="$("${COMPOSE[@]}" ps "$svc" --format '{{.Status}}' || true)"
    if echo "$status" | grep -q healthy; then
      break
    fi
    # openbao may need re-bootstrap unseal
    if [[ "$svc" == openbao ]]; then
      "${COMPOSE[@]}" run --rm --no-deps \
        -e BAO_ADDR=http://openbao:8200 \
        -v "$ROOT/infra/compose/scripts/openbao_bootstrap.sh:/bootstrap.sh:ro" \
        -v "${MEMDOT_SECRETS_DIR:-$ROOT/infra/compose/secrets}/openbao_bootstrap:/bootstrap" \
        -v "${MEMDOT_SECRETS_DIR:-$ROOT/infra/compose/secrets}:/secrets" \
        --entrypoint /bin/sh openbao /bootstrap.sh >/dev/null 2>&1 || true
    fi
    sleep 2
  done
  status="$("${COMPOSE[@]}" ps "$svc" --format '{{.Status}}')"
  echo "$status" | grep -q healthy || { echo "$svc not healthy after restart: $status" >&2; exit 1; }
done

# Full stack restart
"${COMPOSE[@]}" restart
sleep 15
deadline=$((SECONDS + 300))
while (( SECONDS < deadline )); do
  bad=0
  for svc in caddy web core mcp workers model-router postgres seaweedfs keycloak openbao otel-lgtm hatchet-engine hatchet-api; do
    status="$("${COMPOSE[@]}" ps "$svc" --format '{{.Status}}' || echo missing)"
    if ! echo "$status" | grep -q healthy; then
      bad=1
      break
    fi
  done
  [[ "$bad" == "0" ]] && break
  # unseal if needed
  "${COMPOSE[@]}" run --rm --no-deps \
    -e BAO_ADDR=http://openbao:8200 \
    -v "$ROOT/infra/compose/scripts/openbao_bootstrap.sh:/bootstrap.sh:ro" \
    -v "${MEMDOT_SECRETS_DIR:-$ROOT/infra/compose/secrets}/openbao_bootstrap:/bootstrap" \
    -v "${MEMDOT_SECRETS_DIR:-$ROOT/infra/compose/secrets}:/secrets" \
    --entrypoint /bin/sh openbao /bootstrap.sh >/dev/null 2>&1 || true
  sleep 5
done

ROW="$("${COMPOSE[@]}" exec -T postgres \
  psql -U memdot -d memdot_ops -At -c "SELECT checksum FROM ops_durability_fixture WHERE id='$ID';")"
[[ "$ROW" == "$CHECKSUM" ]] || { echo "fixture lost after restart" >&2; exit 1; }

"${COMPOSE[@]}" exec -T postgres \
  psql -U memdot -d memdot_ops -c "DELETE FROM ops_durability_fixture WHERE id='$ID';" >/dev/null

echo "restart_recovery_ok"
