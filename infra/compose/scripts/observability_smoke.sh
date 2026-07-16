#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# Grafana inside otel-lgtm — prefer published loopback port from dev overlay; smoke may not publish it.
# Use docker exec to query Grafana API inside the container.

PROJECT="${COMPOSE_PROJECT_NAME:-memdot}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
COMPOSE=(docker compose --project-name "$PROJECT" --env-file "${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}" "${FILES[@]}")

CID="$("${COMPOSE[@]}" ps -q otel-lgtm)"
[[ -n "$CID" ]] || { echo "otel-lgtm not running" >&2; exit 1; }

# Wait for Grafana API
for _ in $(seq 1 60); do
  if docker exec "$CID" curl -fsS http://127.0.0.1:3000/api/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

SEARCH="$(docker exec "$CID" curl -fsS 'http://127.0.0.1:3000/api/search?type=dash-db')"
echo "$SEARCH" | grep -qi 'memdot' || {
  echo "grafana dashboards not loaded via API: $SEARCH" >&2
  exit 1
}
echo "grafana_dashboards_loaded"

# Denylist: dashboard JSON must not contain forbidden content
DENY='prompt:|user content|set-cookie:|authorization:|BEGIN PRIVATE KEY|password='
if rg -n -i -e "$DENY" "$ROOT/infra/compose/dashboards" ; then
  echo "dashboard denylist hit" >&2
  exit 1
fi

# Log sink denylist sample from compose config render
RENDER="$("${COMPOSE[@]}" config)"
for frag in 'prompt:' 'set-cookie:' 'BEGIN PRIVATE KEY' 'phase2-core-client-secret-not-for-production'; do
  if echo "$RENDER" | grep -Fq "$frag"; then
    echo "telemetry/config denylist hit: $frag" >&2
    exit 1
  fi
done

echo "observability_smoke_ok"
