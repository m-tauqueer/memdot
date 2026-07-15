#!/usr/bin/env bash
set -euo pipefail

# Start all Phase 1 runtime images, verify health endpoints, then tear down.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TAG_SUFFIX="${MEMDOT_IMAGE_TAG:-phase1}"
WEB="memdot-web:${TAG_SUFFIX}"
MCP="memdot-mcp:${TAG_SUFFIX}"
CORE="memdot-core:${TAG_SUFFIX}"
WORKERS="memdot-workers:${TAG_SUFFIX}"
ROUTER="memdot-model-router:${TAG_SUFFIX}"

NAMES=(
  memdot-web-smoke
  memdot-mcp-smoke
  memdot-core-smoke
  memdot-workers-smoke
  memdot-mr-smoke
)

cleanup() {
  docker rm -f "${NAMES[@]}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

cleanup

docker run -d --name memdot-web-smoke -p 13000:3000 "$WEB" >/dev/null
docker run -d --name memdot-mcp-smoke -p 18100:8100 "$MCP" >/dev/null
docker run -d --name memdot-core-smoke -p 18000:8000 "$CORE" >/dev/null
docker run -d --name memdot-workers-smoke -p 18300:8300 "$WORKERS" >/dev/null
docker run -d --name memdot-mr-smoke -p 18200:8200 "$ROUTER" >/dev/null

wait_http() {
  local url="$1"
  local i
  for i in $(seq 1 30); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for $url" >&2
  docker logs "${NAMES[@]}" >&2 || true
  return 1
}

wait_http http://127.0.0.1:13000/api/health
wait_http http://127.0.0.1:18100/health/live
wait_http http://127.0.0.1:18000/health/live
wait_http http://127.0.0.1:18300/health/live
wait_http http://127.0.0.1:18200/health/live

echo "web=$(curl -fsS http://127.0.0.1:13000/api/health)"
echo "mcp=$(curl -fsS http://127.0.0.1:18100/health/ready)"
echo "core=$(curl -fsS http://127.0.0.1:18000/health/ready)"
echo "workers=$(curl -fsS http://127.0.0.1:18300/health/ready)"
echo "model-router=$(curl -fsS http://127.0.0.1:18200/health/ready)"

for name in "${NAMES[@]}"; do
  user="$(docker exec "$name" id -u)"
  if [[ "$user" == "0" ]]; then
    echo "FAIL: $name running as root" >&2
    exit 1
  fi
  echo "runtime-user $name uid=$user"
done

echo "Container health smoke passed."
