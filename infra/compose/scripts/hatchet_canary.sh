#!/usr/bin/env bash
set -euo pipefail

# Real Hatchet canary: token create + durable memdot_ops effects via hatchet-sdk.
# Never prints tokens. Degraded/unavailable returns non-zero.
# Exit 2 is reserved for bounded timeout (distinct from workflow failure).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROJECT="${COMPOSE_PROJECT_NAME:-memdot}"
SECRETS_DIR="${MEMDOT_SECRETS_DIR:-$ROOT/infra/compose/secrets}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
ENV_FILE="${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}"
COMPOSE=(docker compose --project-name "$PROJECT" --env-file "$ENV_FILE" "${FILES[@]}")

TENANT_ID="${HATCHET_TENANT_ID:-707d0855-80ab-4e1f-a156-f1c4546cbf52}"
IDEMPOTENCY_KEY="memdot-canary-$(date -u +%Y%m%d%H%M%S)-$$"
BARRIER_ID="barrier-${IDEMPOTENCY_KEY}"
CANARY_TIMEOUT_SEC="${MEMDOT_CANARY_TIMEOUT_SEC:-120}"
# Outer shell budget exceeds inner canary timeout so Python can report timeout distinctly.
OUTER_TIMEOUT_SEC=$((CANARY_TIMEOUT_SEC + 90))

# shellcheck disable=SC1091
set -a
# shellcheck source=/dev/null
source "${SECRETS_DIR}/postgres.env"
set +a
OPS_DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/memdot_ops"

echo "hatchet_canary_start"

TOKEN_FILE="${SECRETS_DIR}/hatchet_canary.token"
mkdir -p "$(dirname "$TOKEN_FILE")"
ERR_LOG="$(mktemp)"
trap 'rm -f "$ERR_LOG"' EXIT

TOKEN_OUT="$("${COMPOSE[@]}" run --rm --no-deps \
  --entrypoint /hatchet/hatchet-admin \
  hatchet-setup-config \
  token create \
  --config /hatchet/config \
  --tenant-id "$TENANT_ID" \
  --name memdot-canary 2>"$ERR_LOG" | tail -n 1)" || true

if [[ -z "$TOKEN_OUT" || "$TOKEN_OUT" == *"error"* || "$TOKEN_OUT" == *"Usage"* ]]; then
  echo "hatchet_canary_failed reason=token_create" >&2
  sed -n '1,5p' "$ERR_LOG" >&2 || true
  exit 1
fi

printf '%s' "$TOKEN_OUT" >"$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
TOKEN_LEN="${#TOKEN_OUT}"
unset TOKEN_OUT
echo "token_length=$TOKEN_LEN"

run_canary_python() {
  local mode="$1"
  local key="$2"
  local barrier="${3:-}"
  # --user 0 so the one-shot can read the host-owned 0600 token file without weakening perms.
  local -a args=(
    run --rm --no-deps --user 0
    -e HATCHET_CLIENT_TOKEN_FILE=/run/secrets/hatchet_canary.token
    -e HATCHET_CLIENT_TLS_STRATEGY=none
    -e HATCHET_CLIENT_HOST_PORT=hatchet-engine:7070
    -e WORKERS_HATCHET_HOST=hatchet-engine
    -e WORKERS_HATCHET_PORT=7070
    -e MEMDOT_OPS_DATABASE_URL="$OPS_DATABASE_URL"
    -e MEMDOT_CANARY_IDEMPOTENCY_KEY="$key"
    -e MEMDOT_CANARY_TIMEOUT_SEC="$CANARY_TIMEOUT_SEC"
    -e MEMDOT_CANARY_MODE="$mode"
    -v "$TOKEN_FILE:/run/secrets/hatchet_canary.token:ro"
    --entrypoint python
    workers -c '
import os
from pathlib import Path
token = Path(os.environ["HATCHET_CLIENT_TOKEN_FILE"]).read_text().strip()
os.environ["HATCHET_CLIENT_TOKEN"] = token
from memdot_workers.canary_runner import main
raise SystemExit(main())
'
  )
  if [[ -n "$barrier" ]]; then
    args=(
      run --rm --no-deps --user 0
      -e HATCHET_CLIENT_TOKEN_FILE=/run/secrets/hatchet_canary.token
      -e HATCHET_CLIENT_TLS_STRATEGY=none
      -e HATCHET_CLIENT_HOST_PORT=hatchet-engine:7070
      -e WORKERS_HATCHET_HOST=hatchet-engine
      -e WORKERS_HATCHET_PORT=7070
      -e MEMDOT_OPS_DATABASE_URL="$OPS_DATABASE_URL"
      -e MEMDOT_CANARY_IDEMPOTENCY_KEY="$key"
      -e MEMDOT_CANARY_TIMEOUT_SEC="$CANARY_TIMEOUT_SEC"
      -e MEMDOT_CANARY_MODE="$mode"
      -e MEMDOT_CANARY_BARRIER_ID="$barrier"
      -v "$TOKEN_FILE:/run/secrets/hatchet_canary.token:ro"
      --entrypoint python
      workers -c '
import os
from pathlib import Path
token = Path(os.environ["HATCHET_CLIENT_TOKEN_FILE"]).read_text().strip()
os.environ["HATCHET_CLIENT_TOKEN"] = token
from memdot_workers.canary_runner import main
raise SystemExit(main())
'
    )
  fi
  timeout --signal=TERM "$OUTER_TIMEOUT_SEC" "${COMPOSE[@]}" "${args[@]}"
}

echo "== standard canary (idempotency + failure + timeout) =="
set +e
run_canary_python standard "$IDEMPOTENCY_KEY"
CANARY_RC=$?
set -e
if [[ "$CANARY_RC" -eq 124 ]]; then
  echo "hatchet_canary_failed reason=outer_timeout" >&2
  exit 2
fi
if [[ "$CANARY_RC" -eq 2 ]]; then
  echo "hatchet_canary_failed reason=timeout" >&2
  exit 2
fi
[[ "$CANARY_RC" -eq 0 ]] || { echo "hatchet_canary_failed reason=workflow_runner rc=$CANARY_RC" >&2; exit 1; }

echo "== accepted-work barrier across hatchet-engine restart =="
BARRIER_LOG="$(mktemp)"
set +e
# Run barrier canary in background so shell can restart engine while work is outstanding.
timeout --signal=TERM "$OUTER_TIMEOUT_SEC" "${COMPOSE[@]}" run --rm --no-deps --user 0 \
  -e HATCHET_CLIENT_TOKEN_FILE=/run/secrets/hatchet_canary.token \
  -e HATCHET_CLIENT_TLS_STRATEGY=none \
  -e HATCHET_CLIENT_HOST_PORT=hatchet-engine:7070 \
  -e WORKERS_HATCHET_HOST=hatchet-engine \
  -e WORKERS_HATCHET_PORT=7070 \
  -e MEMDOT_OPS_DATABASE_URL="$OPS_DATABASE_URL" \
  -e MEMDOT_CANARY_IDEMPOTENCY_KEY="${IDEMPOTENCY_KEY}-restart" \
  -e MEMDOT_CANARY_TIMEOUT_SEC="$CANARY_TIMEOUT_SEC" \
  -e MEMDOT_CANARY_MODE=barrier \
  -e MEMDOT_CANARY_BARRIER_ID="$BARRIER_ID" \
  -v "$TOKEN_FILE:/run/secrets/hatchet_canary.token:ro" \
  --entrypoint python \
  workers -c '
import os
from pathlib import Path
token = Path(os.environ["HATCHET_CLIENT_TOKEN_FILE"]).read_text().strip()
os.environ["HATCHET_CLIENT_TOKEN"] = token
from memdot_workers.canary_runner import main
raise SystemExit(main())
' >"$BARRIER_LOG" 2>&1 &
BARRIER_PID=$!
set -e

# Wait until barrier step is holding accepted work.
for _ in $(seq 1 90); do
  if grep -q 'barrier_started=true' "$BARRIER_LOG" 2>/dev/null; then
    break
  fi
  if ! kill -0 "$BARRIER_PID" 2>/dev/null; then
    echo "hatchet_canary_failed reason=barrier_exited_early" >&2
    sed -n '1,80p' "$BARRIER_LOG" >&2 || true
    exit 1
  fi
  sleep 1
done
if ! grep -q 'barrier_started=true' "$BARRIER_LOG"; then
  echo "hatchet_canary_failed reason=barrier_not_started" >&2
  sed -n '1,80p' "$BARRIER_LOG" >&2 || true
  kill "$BARRIER_PID" 2>/dev/null || true
  exit 1
fi
ACCEPTED_RUN="$(grep -E '^accepted_run_id=' "$BARRIER_LOG" | tail -n1 | cut -d= -f2-)"
echo "accepted_outstanding_run_id=${ACCEPTED_RUN}"
echo "restarting hatchet-engine while run outstanding"

"${COMPOSE[@]}" restart hatchet-engine
for _ in $(seq 1 60); do
  estatus="$("${COMPOSE[@]}" ps hatchet-engine --format '{{.Status}}' 2>/dev/null || echo missing)"
  if echo "$estatus" | grep -q healthy; then
    break
  fi
  sleep 2
done
estatus="$("${COMPOSE[@]}" ps hatchet-engine --format '{{.Status}}' 2>/dev/null || echo missing)"
echo "$estatus" | grep -q healthy || {
  echo "hatchet_canary_failed reason=engine_unhealthy_after_restart" >&2
  kill "$BARRIER_PID" 2>/dev/null || true
  exit 1
}

# Release barrier so the same outstanding run can finish.
"${COMPOSE[@]}" exec -T postgres \
  psql -U "$POSTGRES_USER" -d memdot_ops -v ON_ERROR_STOP=1 \
  -c "UPDATE ops_canary_barrier SET released = true WHERE barrier_id = '${BARRIER_ID}';" \
  >/dev/null
echo "barrier_released_by_shell=true"

set +e
wait "$BARRIER_PID"
BARRIER_RC=$?
set -e
cat "$BARRIER_LOG"
if [[ "$BARRIER_RC" -eq 124 ]]; then
  echo "hatchet_canary_failed reason=outer_timeout path=barrier" >&2
  rm -f "$BARRIER_LOG"
  exit 2
fi
if [[ "$BARRIER_RC" -eq 2 ]]; then
  echo "hatchet_canary_failed reason=timeout path=barrier" >&2
  rm -f "$BARRIER_LOG"
  exit 2
fi
if [[ "$BARRIER_RC" -ne 0 ]]; then
  echo "hatchet_canary_failed reason=barrier_runner rc=$BARRIER_RC" >&2
  rm -f "$BARRIER_LOG"
  exit 1
fi
grep -q "accepted_work_restart_ok=true" "$BARRIER_LOG" || {
  echo "hatchet_canary_failed reason=missing_restart_ok" >&2
  rm -f "$BARRIER_LOG"
  exit 1
}
grep -q "same_run_id=${ACCEPTED_RUN}" "$BARRIER_LOG" || {
  echo "hatchet_canary_failed reason=run_id_mismatch expected=${ACCEPTED_RUN}" >&2
  rm -f "$BARRIER_LOG"
  exit 1
}
grep -q 'durable_effect_count=1' "$BARRIER_LOG" || {
  echo "hatchet_canary_failed reason=barrier_effect_count" >&2
  rm -f "$BARRIER_LOG"
  exit 1
}
rm -f "$BARRIER_LOG"

echo "idempotency_key_present=true"
echo "hatchet_canary_complete=true"
