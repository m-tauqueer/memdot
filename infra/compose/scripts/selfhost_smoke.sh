#!/usr/bin/env bash
set -euo pipefail

# Bounded end-to-end self-host smoke (Tex off, external telemetry off).
# Uses an isolated runtime directory for secrets/tls/.env so operator files under
# infra/compose are never rewritten. Concurrent smoke is refused via flock.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

# Docker Compose project names must be lowercase alphanumeric / hyphen / underscore.
STAMP="$(date -u +%Y%m%d%H%M%S)"
PROJECT="${MEMDOT_SMOKE_PROJECT:-memdot-smoke-${STAMP}-$$}"
PROJECT="$(echo "$PROJECT" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9_-')"
export MEMDOT_HTTP_PORT="${MEMDOT_HTTP_PORT:-18080}"
export MEMDOT_HTTPS_PORT="${MEMDOT_HTTPS_PORT:-18443}"
export MEMDOT_PUBLIC_HOST="${MEMDOT_PUBLIC_HOST:-localhost}"
export MEMDOT_PUBLIC_URL="https://${MEMDOT_PUBLIC_HOST}:${MEMDOT_HTTPS_PORT}"
export FORCE_REMATERIALIZE="${FORCE_REMATERIALIZE:-1}"
export COMPOSE_PROJECT_NAME="$PROJECT"

COMPOSE_DIR="$ROOT/infra/compose"
# Fixed path outside any project-specific log dir — CI cleanup reads this.
PROJECT_NAME_FILE="${MEMDOT_SMOKE_PROJECT_NAME_FILE:-/tmp/memdot-smoke-project-name}"
LOCK_FILE="${MEMDOT_SMOKE_LOCK_FILE:-/tmp/memdot-selfhost-smoke.lock}"
RUNTIME_ROOT="${MEMDOT_SMOKE_RUNTIME_DIR:-/tmp/${PROJECT}-runtime}"
LOG_DIR="${MEMDOT_SMOKE_LOG_DIR:-/tmp/${PROJECT}-logs}"
export MEMDOT_SECRETS_DIR="${RUNTIME_ROOT}/secrets"
export MEMDOT_TLS_DIR="${RUNTIME_ROOT}/tls"
export MEMDOT_ENV_FILE="${RUNTIME_ROOT}/.env"

mkdir -p "$LOG_DIR" "$RUNTIME_ROOT"
chmod 700 "$RUNTIME_ROOT"

# Exclusive lock: refuse concurrent smoke runs.
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "selfhost_smoke_rejected reason=concurrent_smoke lock=$LOCK_FILE" >&2
  exit 1
fi
echo "smoke_lock_acquired file=$LOCK_FILE"

# Record project name for CI cleanup (plain file, validated pattern).
printf '%s\n' "$PROJECT" >"$PROJECT_NAME_FILE"
chmod 600 "$PROJECT_NAME_FILE"
echo "project_name=${PROJECT}" | tee "$LOG_DIR/project_name.txt"

# Snapshot operator paths for byte-identity assertions (read-only; never restore over them).
OPERATOR_SECRETS="$COMPOSE_DIR/secrets"
OPERATOR_TLS="$COMPOSE_DIR/tls"
OPERATOR_ENV="$COMPOSE_DIR/.env"
OPERATOR_HASH_BEFORE="$LOG_DIR/operator-before.sha256"
{
  if [[ -d "$OPERATOR_SECRETS" ]]; then
    find "$OPERATOR_SECRETS" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum 2>/dev/null || true
  fi
  if [[ -d "$OPERATOR_TLS" ]]; then
    find "$OPERATOR_TLS" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum 2>/dev/null || true
  fi
  if [[ -f "$OPERATOR_ENV" ]]; then
    sha256sum "$OPERATOR_ENV" 2>/dev/null || true
  fi
} >"$OPERATOR_HASH_BEFORE"

assert_operator_unchanged() {
  local after="$LOG_DIR/operator-after.sha256"
  {
    if [[ -d "$OPERATOR_SECRETS" ]]; then
      find "$OPERATOR_SECRETS" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum 2>/dev/null || true
    fi
    if [[ -d "$OPERATOR_TLS" ]]; then
      find "$OPERATOR_TLS" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum 2>/dev/null || true
    fi
    if [[ -f "$OPERATOR_ENV" ]]; then
      sha256sum "$OPERATOR_ENV" 2>/dev/null || true
    fi
  } >"$after"
  if ! cmp -s "$OPERATOR_HASH_BEFORE" "$after"; then
    echo "operator_files_mutated=true" >&2
    diff -u "$OPERATOR_HASH_BEFORE" "$after" >&2 || true
    return 1
  fi
  echo "operator_files_byte_identical=true"
}

COMPOSE=(
  docker compose
  --project-name "$PROJECT"
  --env-file "$MEMDOT_ENV_FILE"
  -f "$COMPOSE_DIR/compose.yaml"
  -f "$COMPOSE_DIR/compose.test.yaml"
)

REQUIRED_HEALTHY=(
  caddy web core mcp workers model-router postgres seaweedfs keycloak openbao
  otel-lgtm hatchet-engine hatchet-api
)
REQUIRED_ONESHOT=(hatchet-migrate hatchet-setup-config openbao-bootstrap)

cleanup_runtime() {
  # Only remove this smoke's generated runtime — never operator infra/compose secrets.
  if [[ "${MEMDOT_SMOKE_KEEP_RUNTIME:-0}" != "1" && -d "$RUNTIME_ROOT" ]]; then
    case "$RUNTIME_ROOT" in
      /tmp/memdot-smoke-*-runtime | /tmp/"${PROJECT}"-runtime)
        rm -rf "$RUNTIME_ROOT"
        echo "smoke_runtime_removed=$RUNTIME_ROOT"
        ;;
      *)
        echo "smoke_runtime_cleanup_skipped path=$RUNTIME_ROOT" >&2
        ;;
    esac
  fi
}

cleanup() {
  local code=$?
  if [[ "$code" -ne 0 ]]; then
    echo "== diagnostics ==" >&2
    "${COMPOSE[@]}" ps >"$LOG_DIR/ps.txt" 2>&1 || true
    "${COMPOSE[@]}" logs --no-color --tail=200 >"$LOG_DIR/logs.txt" 2>&1 || true
    echo "diagnostics_dir=$LOG_DIR" >&2
  fi
  if [[ "${MEMDOT_SMOKE_KEEP:-0}" != "1" ]]; then
    "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  fi
  assert_operator_unchanged || code=1
  cleanup_runtime
  # Clear project-name file only after successful cleanup of this project.
  if [[ "$code" -eq 0 && -f "$PROJECT_NAME_FILE" ]]; then
    if [[ "$(tr -d '[:space:]' <"$PROJECT_NAME_FILE")" == "$PROJECT" ]]; then
      rm -f "$PROJECT_NAME_FILE"
    fi
  fi
  exit "$code"
}
trap cleanup EXIT

echo "== materialize isolated secrets + TLS (operator paths untouched) =="
mkdir -p "$MEMDOT_SECRETS_DIR/openbao_bootstrap"
chmod 700 "$MEMDOT_SECRETS_DIR" "$MEMDOT_SECRETS_DIR/openbao_bootstrap"
# Transit token: 0600 from the start (never 0666/0777).
: >"$MEMDOT_SECRETS_DIR/openbao_transit_token"
chmod 600 "$MEMDOT_SECRETS_DIR/openbao_transit_token"

MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" \
  MEMDOT_TLS_DIR="$MEMDOT_TLS_DIR" \
  MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  FORCE_REMATERIALIZE=1 \
  COMPOSE_PROJECT_NAME="$PROJECT" \
  MEMDOT_PUBLIC_HOST="$MEMDOT_PUBLIC_HOST" \
  MEMDOT_HTTP_PORT="$MEMDOT_HTTP_PORT" \
  MEMDOT_HTTPS_PORT="$MEMDOT_HTTPS_PORT" \
  MEMDOT_PUBLIC_URL="$MEMDOT_PUBLIC_URL" \
  bash "$COMPOSE_DIR/scripts/materialize_local_secrets.sh"

# Ensure .env carries bind overrides for compose interpolation.
cat >"$MEMDOT_ENV_FILE" <<EOF
COMPOSE_PROJECT_NAME=${PROJECT}
MEMDOT_PUBLIC_HOST=${MEMDOT_PUBLIC_HOST}
MEMDOT_HTTP_PORT=${MEMDOT_HTTP_PORT}
MEMDOT_HTTPS_PORT=${MEMDOT_HTTPS_PORT}
MEMDOT_PUBLIC_URL=${MEMDOT_PUBLIC_URL}
MEMDOT_SECRETS_DIR=${MEMDOT_SECRETS_DIR}
MEMDOT_TLS_DIR=${MEMDOT_TLS_DIR}
HATCHET_COOKIE_DOMAIN=${MEMDOT_PUBLIC_HOST}
HATCHET_SERVER_URL=http://127.0.0.1:18080
OTEL_SDK_DISABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=
EOF
chmod 600 "$MEMDOT_ENV_FILE"

# Re-materialize realm/app env against smoke public URL into the same isolated dirs.
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" \
  MEMDOT_TLS_DIR="$MEMDOT_TLS_DIR" \
  MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  FORCE_REMATERIALIZE=1 \
  COMPOSE_PROJECT_NAME="$PROJECT" \
  MEMDOT_PUBLIC_HOST="$MEMDOT_PUBLIC_HOST" \
  MEMDOT_HTTP_PORT="$MEMDOT_HTTP_PORT" \
  MEMDOT_HTTPS_PORT="$MEMDOT_HTTPS_PORT" \
  MEMDOT_PUBLIC_URL="$MEMDOT_PUBLIC_URL" \
  bash "$COMPOSE_DIR/scripts/materialize_local_secrets.sh"

# Harden bootstrap + transit token permissions after materialize.
chmod 700 "$MEMDOT_SECRETS_DIR/openbao_bootstrap"
find "$MEMDOT_SECRETS_DIR/openbao_bootstrap" -type f -exec chmod 600 {} \;
chmod 600 "$MEMDOT_SECRETS_DIR/openbao_transit_token"
# Refuse world/group readable secrets.
if find "$MEMDOT_SECRETS_DIR" -type f -perm /0077 | grep -q .; then
  echo "secret_permissions_too_open under $MEMDOT_SECRETS_DIR" >&2
  find "$MEMDOT_SECRETS_DIR" -type f -perm /0077 -ls >&2 || true
  exit 1
fi

SOURCE_HASH="$(git rev-parse HEAD)-$(git status --porcelain | sha256sum | awk '{print $1}')"
export SOURCE_HASH

echo "== compose policy =="
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_TLS_DIR="$MEMDOT_TLS_DIR" \
  uv run python "$COMPOSE_DIR/scripts/validate_compose_policy.py"

echo "== build current sources (--build --force-recreate) =="
"${COMPOSE[@]}" build \
  --build-arg "MEMDOT_SOURCE_HASH=${SOURCE_HASH}" \
  web core mcp workers model-router
if ! SOURCE_HASH="$SOURCE_HASH" "${COMPOSE[@]}" up -d --build --force-recreate --remove-orphans; then
  echo "compose up returned non-zero; will retry one-shot services if needed"
fi

ensure_oneshot_success() {
  local svc="$1"
  local status attempt=0
  status="$("${COMPOSE[@]}" ps -a "$svc" --format '{{.Status}}' 2>/dev/null || echo missing)"
  if echo "$status" | grep -q 'Exited (0)'; then
    return 0
  fi
  echo "oneshot retry: $svc (was: $status)"
  "${COMPOSE[@]}" rm -f "$svc" >/dev/null 2>&1 || true
  while (( attempt < 5 )); do
    attempt=$((attempt + 1))
    sleep 5
    if "${COMPOSE[@]}" up --no-deps --force-recreate -d "$svc"; then
      local i=0
      while (( i < 90 )); do
        status="$("${COMPOSE[@]}" ps -a "$svc" --format '{{.Status}}' 2>/dev/null || echo missing)"
        if echo "$status" | grep -q 'Exited (0)'; then
          echo "oneshot retry ok: $svc"
          return 0
        fi
        if echo "$status" | grep -Eq 'Exited \([1-9]|Restarting|Dead'; then
          echo "oneshot attempt $attempt failed: $svc status=$status" >&2
          "${COMPOSE[@]}" logs --no-color --tail=80 "$svc" >"$LOG_DIR/${svc}.attempt${attempt}.log" 2>&1 || true
          break
        fi
        sleep 2
        i=$((i + 1))
      done
    fi
    "${COMPOSE[@]}" rm -f "$svc" >/dev/null 2>&1 || true
  done
  echo "oneshot retry failed: $svc" >&2
  "${COMPOSE[@]}" logs --no-color --tail=120 "$svc" >"$LOG_DIR/${svc}.final.log" 2>&1 || true
  return 1
}

for svc in hatchet-migrate hatchet-setup-config openbao-bootstrap; do
  ensure_oneshot_success "$svc" || { echo "oneshot failed after retry: $svc" >&2; exit 1; }
done

# Transit token must remain 0600 and owned by Core uid when bootstrap chowns it.
TOKEN_MODE="$(stat -c '%a' "$MEMDOT_SECRETS_DIR/openbao_transit_token" 2>/dev/null || echo missing)"
[[ "$TOKEN_MODE" == "600" ]] || {
  echo "transit_token_mode_expected_600 got=$TOKEN_MODE" >&2
  exit 1
}

assert_image_freshness() {
  local svc="$1"
  local cid
  cid="$("${COMPOSE[@]}" ps -q "$svc")"
  [[ -n "$cid" ]] || { echo "missing container for $svc" >&2; return 1; }
  local created label
  created="$(docker inspect -f '{{.Created}}' "$cid")"
  label="$(docker inspect -f '{{index .Config.Labels "memdot.source_hash"}}' "$cid" 2>/dev/null || true)"
  echo "freshness $svc created=$created source_hash_label=${label:-none}"
  if [[ "$svc" =~ ^(web|core|mcp|workers|model-router)$ ]]; then
    [[ -n "$label" && "$label" != "<no value>" ]] || {
      echo "missing memdot.source_hash label on $svc" >&2
      return 1
    }
    [[ "$label" == "$SOURCE_HASH" ]] || {
      echo "stale image for $svc label=$label expected=$SOURCE_HASH" >&2
      return 1
    }
  fi
}

echo "== wait for exact health =="
deadline=$((SECONDS + 900))
last_report=0
while (( SECONDS < deadline )); do
  ok=1
  pending=()
  for svc in "${REQUIRED_HEALTHY[@]}"; do
    status="$("${COMPOSE[@]}" ps "$svc" --format '{{.Status}}' 2>/dev/null || echo missing)"
    if ! echo "$status" | grep -q '(healthy)'; then
      ok=0
      pending+=("${svc}=${status}")
    fi
  done
  for svc in "${REQUIRED_ONESHOT[@]}"; do
    status="$("${COMPOSE[@]}" ps -a "$svc" --format '{{.Status}}' 2>/dev/null || echo missing)"
    if ! echo "$status" | grep -q 'Exited (0)'; then
      ok=0
      pending+=("${svc}=${status}")
    fi
  done
  if (( SECONDS - last_report >= 30 )); then
    echo "health_wait pending: ${pending[*]:-none}"
    last_report=$SECONDS
  fi
  if [[ "$ok" == "1" ]]; then
    break
  fi
  sleep 10
done

"${COMPOSE[@]}" ps -a
for svc in "${REQUIRED_HEALTHY[@]}"; do
  status="$("${COMPOSE[@]}" ps "$svc" --format '{{.Status}}')"
  echo "$status" | grep -q '(healthy)' || { echo "service not healthy: $svc status=$status" >&2; exit 1; }
  assert_image_freshness "$svc"
done
for svc in "${REQUIRED_ONESHOT[@]}"; do
  status="$("${COMPOSE[@]}" ps -a "$svc" --format '{{.Status}}')"
  echo "$status" | grep -q 'Exited (0)' || { echo "oneshot failed: $svc status=$status" >&2; exit 1; }
done

CA="$MEMDOT_TLS_DIR/ca.crt"
[[ -f "$CA" ]] || { echo "missing CA cert" >&2; exit 1; }

echo "== TLS/routing with cacert (no -k) =="
curl -fsS --cacert "$CA" "https://127.0.0.1:${MEMDOT_HTTPS_PORT}/healthz" | grep -q ok
curl -fsS --cacert "$CA" "https://127.0.0.1:${MEMDOT_HTTPS_PORT}/api/health" >/dev/null
curl -fsS --cacert "$CA" "https://127.0.0.1:${MEMDOT_HTTPS_PORT}/mcp/health/live" >/dev/null

echo "== OIDC discovery / JWKS / audiences =="
DISC="$(curl -fsS --cacert "$CA" "https://127.0.0.1:${MEMDOT_HTTPS_PORT}/realms/memdot/.well-known/openid-configuration")"
echo "$DISC" | grep -q "\"issuer\":\"${MEMDOT_PUBLIC_URL}/realms/memdot\""
curl -fsS --cacert "$CA" "https://127.0.0.1:${MEMDOT_HTTPS_PORT}/realms/memdot/protocol/openid-connect/certs" | grep -q '"keys"'

echo "== OpenBao Transit live round-trip =="
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/openbao_transit_smoke.sh"

echo "== Hatchet canary =="
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/hatchet_canary.sh"

echo "== SeaweedFS S3 durability =="
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/seaweed_durability_smoke.sh"

echo "== PostgreSQL backup/restore =="
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/postgres_durability_smoke.sh"
BACKUP_DIR="$LOG_DIR/backups"
mkdir -p "$BACKUP_DIR"
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/postgres_backup.sh" "$BACKUP_DIR"
DUMP="$(ls -1t "$BACKUP_DIR"/*.dump | head -1)"
RESTORE_DB="memdot_restore_${PROJECT##*-}"
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/postgres_restore.sh" "$DUMP" "$RESTORE_DB"
CHECKSUM_BEFORE="$("${COMPOSE[@]}" exec -T postgres psql -U memdot -d memdot_ops -At -c \
  "SELECT coalesce(sum(hashtext(id || payload || checksum)),0) FROM ops_durability_fixture;")"
CHECKSUM_AFTER="$("${COMPOSE[@]}" exec -T postgres psql -U memdot -d "$RESTORE_DB" -At -c \
  "SELECT coalesce(sum(hashtext(id || payload || checksum)),0) FROM ops_durability_fixture;")"
[[ "$CHECKSUM_BEFORE" == "$CHECKSUM_AFTER" ]] || {
  echo "restore checksum mismatch before=$CHECKSUM_BEFORE after=$CHECKSUM_AFTER" >&2
  exit 1
}
"${COMPOSE[@]}" exec -T postgres psql -U memdot -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS \"$RESTORE_DB\";"
if bash "$COMPOSE_DIR/scripts/postgres_restore.sh" "$DUMP" memdot_ops; then
  echo "wrong-target restore should fail" >&2
  exit 1
fi
if bash "$COMPOSE_DIR/scripts/postgres_restore.sh" "$DUMP" memdot; then
  echo "wrong-target restore should fail" >&2
  exit 1
fi
echo junk >"$LOG_DIR/bad.dump"
if bash "$COMPOSE_DIR/scripts/postgres_restore.sh" "$LOG_DIR/bad.dump" "$RESTORE_DB"; then
  echo "corrupt restore should fail" >&2
  exit 1
fi

echo "== migration seam =="
bash "$COMPOSE_DIR/scripts/migration_job.sh" self_host

echo "== restart recovery =="
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/restart_recovery_smoke.sh"

echo "== dependency failure recovery =="
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/dependency_failure_smoke.sh"

echo "== dashboards + telemetry denylist =="
MEMDOT_SECRETS_DIR="$MEMDOT_SECRETS_DIR" MEMDOT_ENV_FILE="$MEMDOT_ENV_FILE" \
  bash "$COMPOSE_DIR/scripts/observability_smoke.sh"

echo "== tex absent / telemetry off =="
if "${COMPOSE[@]}" config --services | grep -qx tex; then
  echo "tex present" >&2
  exit 1
fi
if "${COMPOSE[@]}" config | grep -E 'OTEL_EXPORTER_OTLP_ENDPOINT: [^"[:space:]]+' | grep -v 'OTEL_EXPORTER_OTLP_ENDPOINT: ""' >/dev/null; then
  echo "unexpected otlp endpoint" >&2
  exit 1
fi

echo "selfhost_smoke_passed project=${PROJECT}"
