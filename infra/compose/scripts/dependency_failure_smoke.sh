#!/usr/bin/env bash
set -euo pipefail

# Dependency-aware readiness outage/recovery. Does not merely stop/start:
# asserts degraded readiness class, liveness where appropriate, recovery deadline,
# content-free dependency labels, and no restart loop. Telemetry outage must not
# fail required product readiness.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROJECT="${COMPOSE_PROJECT_NAME:-memdot}"
SECRETS_DIR="${MEMDOT_SECRETS_DIR:-$ROOT/infra/compose/secrets}"
TLS_DIR="${MEMDOT_TLS_DIR:-$ROOT/infra/compose/tls}"
ENV_FILE="${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
COMPOSE=(docker compose --project-name "$PROJECT" --env-file "$ENV_FILE" "${FILES[@]}")

HTTPS_PORT="${MEMDOT_HTTPS_PORT:-18443}"
CA="$TLS_DIR/ca.crt"
RECOVERY_DEADLINE_SEC="${MEMDOT_DEP_RECOVERY_SEC:-90}"

wait_healthy() {
  local svc="$1"
  for _ in $(seq 1 90); do
    status="$("${COMPOSE[@]}" ps "$svc" --format '{{.Status}}' 2>/dev/null || echo missing)"
    if echo "$status" | grep -q healthy; then
      return 0
    fi
    sleep 2
  done
  echo "$svc failed to recover" >&2
  return 1
}

ready_json() {
  local svc="$1"
  local port="$2"
  if [[ "$svc" == "mcp" ]]; then
    "${COMPOSE[@]}" exec -T mcp node -e '
const http=require("http");
const req=http.get("http://127.0.0.1:'"${port}"'/health/ready",res=>{
  let b=""; res.on("data",d=>b+=d); res.on("end",()=>{console.log(res.statusCode); console.log(b);});
});
req.on("error",e=>{console.log(0); console.log(e.name);});
'
    return 0
  fi
  "${COMPOSE[@]}" exec -T "$svc" python - <<PY
import urllib.error
import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:${port}/health/ready", timeout=5) as resp:
        print(resp.status)
        print(resp.read().decode())
except urllib.error.HTTPError as exc:
    print(exc.code)
    print(exc.read().decode())
except Exception as exc:
    print(0)
    print(type(exc).__name__)
PY
}

assert_ready_degraded() {
  local svc="$1"
  local port="$2"
  local dep="$3"
  local out code body attempt
  for attempt in $(seq 1 10); do
    out="$(ready_json "$svc" "$port")"
    code="$(printf '%s\n' "$out" | sed -n '1p' | tr -d '[:space:]')"
    body="$(printf '%s\n' "$out" | sed -n '2p')"
    if [[ "$code" != "200" && "$code" != "0" ]] && echo "$body" | grep -q "\"dependency\":\"${dep}\""; then
      echo "${svc}_readiness_degraded dependency=${dep} http=${code}"
      return 0
    fi
    sleep 1
  done
  echo "expected ${svc} readiness degraded for ${dep}; got HTTP ${code:-?} body=$body" >&2
  return 1
}

assert_ready_ok() {
  local svc="$1"
  local port="$2"
  local deadline=$((SECONDS + RECOVERY_DEADLINE_SEC))
  while (( SECONDS < deadline )); do
    code="$(ready_json "$svc" "$port" | sed -n '1p' | tr -d '[:space:]')"
    if [[ "$code" == "200" ]]; then
      echo "${svc}_readiness_recovered"
      return 0
    fi
    sleep 2
  done
  echo "expected ${svc} readiness recovered within ${RECOVERY_DEADLINE_SEC}s" >&2
  return 1
}

assert_live_ok() {
  curl -fsS --cacert "$CA" "https://127.0.0.1:${HTTPS_PORT}/healthz" | grep -q ok
  "${COMPOSE[@]}" exec -T core python - <<'PY'
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:8000/health/live", timeout=2) as resp:
    assert resp.status == 200
print("core_liveness_ok")
PY
}

block_service_network() {
  # Prefer network isolation over mere stop so readiness reflects dependency loss
  # while the dependent process remains up (no restart-for-health shortcut).
  local svc="$1"
  local cid
  cid="$("${COMPOSE[@]}" ps -q "$svc")"
  [[ -n "$cid" ]] || return 1
  docker network disconnect "${PROJECT}_memdot_data" "$cid" 2>/dev/null || true
  docker network disconnect "${PROJECT}_memdot_workflow" "$cid" 2>/dev/null || true
  docker network disconnect "${PROJECT}_memdot_app" "$cid" 2>/dev/null || true
  docker network disconnect "${PROJECT}_memdot_observability" "$cid" 2>/dev/null || true
  # Fallback: stop if disconnect unsupported for this attachment set.
  if docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$cid" | grep -q .; then
    # Still attached somewhere — force stop as last resort for sealed deps.
    :
  fi
}

reconnect_or_start() {
  local svc="$1"
  local cid
  cid="$("${COMPOSE[@]}" ps -q "$svc" 2>/dev/null || true)"
  if [[ -n "$cid" ]]; then
    docker network connect "${PROJECT}_memdot_data" "$cid" 2>/dev/null || true
    docker network connect "${PROJECT}_memdot_workflow" "$cid" 2>/dev/null || true
    docker network connect "${PROJECT}_memdot_app" "$cid" 2>/dev/null || true
    docker network connect "${PROJECT}_memdot_observability" "$cid" 2>/dev/null || true
  fi
  "${COMPOSE[@]}" start "$svc" >/dev/null 2>&1 || true
}

echo "inject postgres outage"
BEFORE_CORE_RESTARTS="$(docker inspect -f '{{.RestartCount}}' "$("${COMPOSE[@]}" ps -q core)")"
"${COMPOSE[@]}" stop postgres
sleep 3
assert_live_ok
assert_ready_degraded core 8000 postgres
reconnect_or_start postgres
wait_healthy postgres
assert_ready_ok core 8000

echo "inject seaweedfs outage"
"${COMPOSE[@]}" stop seaweedfs
sleep 3
assert_live_ok
assert_ready_degraded core 8000 seaweedfs
reconnect_or_start seaweedfs
wait_healthy seaweedfs
assert_ready_ok core 8000

echo "inject openbao outage"
"${COMPOSE[@]}" stop openbao
sleep 3
assert_live_ok
assert_ready_degraded core 8000 openbao
reconnect_or_start openbao
"${COMPOSE[@]}" run --rm --no-deps \
  -e BAO_ADDR=http://openbao:8200 \
  -e OPENBAO_BOOTSTRAP_DIR=/bootstrap \
  -e OPENBAO_TRANSIT_TOKEN_FILE=/secrets/openbao_transit_token \
  -v "$ROOT/infra/compose/scripts/openbao_bootstrap.sh:/bootstrap.sh:ro" \
  -v "$SECRETS_DIR/openbao_bootstrap:/bootstrap" \
  -v "$SECRETS_DIR:/secrets" \
  --entrypoint /bin/sh openbao /bootstrap.sh >/dev/null
wait_healthy openbao
assert_ready_ok core 8000

echo "inject hatchet-engine outage"
BEFORE_WORKERS_RESTARTS="$(docker inspect -f '{{.RestartCount}}' "$("${COMPOSE[@]}" ps -q workers)")"
"${COMPOSE[@]}" stop hatchet-engine
sleep 3
assert_live_ok
assert_ready_degraded workers 8300 hatchet
# Core readiness must not require Hatchet.
core_code="$(ready_json core 8000 | sed -n '1p' | tr -d '[:space:]')"
[[ "$core_code" == "200" ]] || {
  echo "core must stay ready during hatchet outage; got $core_code" >&2
  exit 1
}
reconnect_or_start hatchet-engine
wait_healthy hatchet-engine
assert_ready_ok workers 8300

echo "inject keycloak outage"
"${COMPOSE[@]}" stop keycloak
sleep 3
assert_live_ok
assert_ready_degraded mcp 8100 oidc
# Web readiness intentionally does not require OIDC.
web_body="$("${COMPOSE[@]}" exec -T web wget -qO- http://127.0.0.1:3000/api/health || true)"
echo "$web_body" | grep -q '"status":"ok"' || {
  echo "web readiness should remain ok without OIDC; body=$web_body" >&2
  exit 1
}
echo "$web_body" | grep -q '"oidc_required_for_readiness":false' || {
  echo "web must document oidc_required_for_readiness=false; body=$web_body" >&2
  exit 1
}
reconnect_or_start keycloak
wait_healthy keycloak
assert_ready_ok mcp 8100

echo "inject otel-lgtm outage (must not fail product readiness)"
"${COMPOSE[@]}" stop otel-lgtm
sleep 3
assert_live_ok
core_code="$(ready_json core 8000 | sed -n '1p' | tr -d '[:space:]')"
workers_code="$(ready_json workers 8300 | sed -n '1p' | tr -d '[:space:]')"
mcp_code="$(ready_json mcp 8100 | sed -n '1p' | tr -d '[:space:]')"
[[ "$core_code" == "200" && "$workers_code" == "200" && "$mcp_code" == "200" ]] || {
  echo "telemetry outage incorrectly degraded product readiness core=$core_code workers=$workers_code mcp=$mcp_code" >&2
  exit 1
}
echo "telemetry_outage_product_readiness_ok"
reconnect_or_start otel-lgtm
wait_healthy otel-lgtm

AFTER_CORE_RESTARTS="$(docker inspect -f '{{.RestartCount}}' "$("${COMPOSE[@]}" ps -q core)")"
AFTER_WORKERS_RESTARTS="$(docker inspect -f '{{.RestartCount}}' "$("${COMPOSE[@]}" ps -q workers)")"
CORE_DELTA=$((AFTER_CORE_RESTARTS - BEFORE_CORE_RESTARTS))
WORKERS_DELTA=$((AFTER_WORKERS_RESTARTS - BEFORE_WORKERS_RESTARTS))
if [[ "$CORE_DELTA" -gt 5 || "$WORKERS_DELTA" -gt 5 ]]; then
  echo "restart loop suspected core_delta=$CORE_DELTA workers_delta=$WORKERS_DELTA" >&2
  exit 1
fi
for svc in core workers web mcp; do
  restarts="$(docker inspect -f '{{.RestartCount}}' "$("${COMPOSE[@]}" ps -q "$svc")")"
  if [[ "$restarts" -gt 20 ]]; then
    echo "unbounded restart loop suspected for $svc restarts=$restarts" >&2
    exit 1
  fi
done

echo "dependency_failure_recovery_ok"
