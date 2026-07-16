#!/usr/bin/env bash
set -euo pipefail

# Materialize ignored local Compose secrets, TLS, and runtime config from templates.
# Cryptographically random per-install values. Never prints secrets.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# Allow disposable smoke / alternate runtimes without rewriting operator paths.
SECRETS="${MEMDOT_SECRETS_DIR:-$COMPOSE_DIR/secrets}"
TLS="${MEMDOT_TLS_DIR:-$COMPOSE_DIR/tls}"
ENV_OUT="${MEMDOT_ENV_FILE:-$COMPOSE_DIR/.env}"
CONFIG="$COMPOSE_DIR/config"
BOOTSTRAP_DIR="$SECRETS/openbao_bootstrap"

PUBLIC_HOST="${MEMDOT_PUBLIC_HOST:-localhost}"
HTTP_PORT="${MEMDOT_HTTP_PORT:-8080}"
HTTPS_PORT="${MEMDOT_HTTPS_PORT:-8443}"
PUBLIC_URL="${MEMDOT_PUBLIC_URL:-https://${PUBLIC_HOST}:${HTTPS_PORT}}"
OIDC_ISSUER="${PUBLIC_URL}/realms/memdot"

rand_secret() {
  # URL-safe alphanumeric only so DATABASE_URL / JDBC URLs never break on /+@.
  openssl rand -hex 24
}

should_materialize() {
  local target="$1"
  [[ "${FORCE_REMATERIALIZE:-}" == "1" || ! -f "$target" ]]
}

mkdir -p "$SECRETS" "$TLS" "$BOOTSTRAP_DIR"
chmod 700 "$BOOTSTRAP_DIR"
touch "$BOOTSTRAP_DIR/.gitkeep"

bash "$SCRIPT_DIR/generate_tls.sh" "$TLS"

if should_materialize "$ENV_OUT"; then
  cat >"$ENV_OUT" <<EOF
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-memdot}
MEMDOT_PUBLIC_HOST=${PUBLIC_HOST}
MEMDOT_HTTP_PORT=${HTTP_PORT}
MEMDOT_HTTPS_PORT=${HTTPS_PORT}
MEMDOT_PUBLIC_URL=${PUBLIC_URL}
MEMDOT_SECRETS_DIR=${SECRETS}
MEMDOT_TLS_DIR=${TLS}
HATCHET_COOKIE_DOMAIN=${PUBLIC_HOST}
HATCHET_SERVER_URL=http://127.0.0.1:18080
OTEL_SDK_DISABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=
EOF
  chmod 600 "$ENV_OUT"
fi

# shellcheck disable=SC1091
set -a
# shellcheck source=/dev/null
source "$ENV_OUT"
set +a
PUBLIC_URL="${MEMDOT_PUBLIC_URL}"
OIDC_ISSUER="${PUBLIC_URL}/realms/memdot"

POSTGRES_PASSWORD="$(rand_secret)"
if [[ -f "$SECRETS/postgres.env" && "${FORCE_REMATERIALIZE:-}" != "1" ]]; then
  POSTGRES_PASSWORD="$(grep '^POSTGRES_PASSWORD=' "$SECRETS/postgres.env" | cut -d= -f2-)"
fi

if should_materialize "$SECRETS/postgres.env"; then
  printf 'POSTGRES_USER=memdot\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=memdot\n' "$POSTGRES_PASSWORD" >"$SECRETS/postgres.env"
  chmod 600 "$SECRETS/postgres.env"
fi

MIGRATE_PASSWORD="$(rand_secret)"
CORE_DB_PASSWORD="$(rand_secret)"
TEST_ADMIN_PASSWORD="$(rand_secret)"
TENANT_CONTEXT_SIGNING_KEY="$(rand_secret)$(rand_secret)"
if [[ -f "$SECRETS/db-roles.env" && "${FORCE_REMATERIALIZE:-}" != "1" ]]; then
  MIGRATE_PASSWORD="$(grep '^MEMDOT_MIGRATE_PASSWORD=' "$SECRETS/db-roles.env" | cut -d= -f2-)"
  CORE_DB_PASSWORD="$(grep '^MEMDOT_CORE_PASSWORD=' "$SECRETS/db-roles.env" | cut -d= -f2-)"
  TEST_ADMIN_PASSWORD="$(grep '^MEMDOT_TEST_ADMIN_PASSWORD=' "$SECRETS/db-roles.env" | cut -d= -f2-)"
  TENANT_CONTEXT_SIGNING_KEY="$(grep '^MEMDOT_TENANT_CONTEXT_SIGNING_KEY=' "$SECRETS/db-roles.env" | cut -d= -f2-)"
fi
if should_materialize "$SECRETS/db-roles.env"; then
  cat >"$SECRETS/db-roles.env" <<EOF
MEMDOT_MIGRATE_PASSWORD=${MIGRATE_PASSWORD}
MEMDOT_CORE_PASSWORD=${CORE_DB_PASSWORD}
MEMDOT_TEST_ADMIN_PASSWORD=${TEST_ADMIN_PASSWORD}
MEMDOT_TENANT_CONTEXT_SIGNING_KEY=${TENANT_CONTEXT_SIGNING_KEY}
MEMDOT_MIGRATION_DATABASE_URL=postgres://memdot_migrate:${MIGRATE_PASSWORD}@postgres:5432/memdot
MEMDOT_TEST_ADMIN_DATABASE_URL=postgres://memdot_test_admin:${TEST_ADMIN_PASSWORD}@postgres:5432/memdot
MEMDOT_BOOTSTRAP_DATABASE_URL=postgres://memdot:${POSTGRES_PASSWORD}@postgres:5432/memdot
EOF
  chmod 600 "$SECRETS/db-roles.env"
else
  set -a
  # shellcheck source=/dev/null
  source "$SECRETS/db-roles.env"
  set +a
  MIGRATE_PASSWORD="${MEMDOT_MIGRATE_PASSWORD}"
  CORE_DB_PASSWORD="${MEMDOT_CORE_PASSWORD}"
  TEST_ADMIN_PASSWORD="${MEMDOT_TEST_ADMIN_PASSWORD}"
  TENANT_CONTEXT_SIGNING_KEY="${MEMDOT_TENANT_CONTEXT_SIGNING_KEY}"
fi

if should_materialize "$SECRETS/hatchet.env"; then
  printf 'DATABASE_URL=postgres://memdot:%s@postgres:5432/hatchet?sslmode=disable\n' "$POSTGRES_PASSWORD" >"$SECRETS/hatchet.env"
  chmod 600 "$SECRETS/hatchet.env"
fi

KEYCLOAK_ADMIN_PASSWORD="$(rand_secret)"
KEYCLOAK_CORE_CLIENT_SECRET="$(rand_secret)"
KEYCLOAK_MCP_CLIENT_SECRET="$(rand_secret)"
if should_materialize "$SECRETS/keycloak.env"; then
  cat >"$SECRETS/keycloak.env" <<EOF
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}
KC_DB_USERNAME=memdot
KC_DB_PASSWORD=${POSTGRES_PASSWORD}
KEYCLOAK_CORE_CLIENT_SECRET=${KEYCLOAK_CORE_CLIENT_SECRET}
KEYCLOAK_MCP_CLIENT_SECRET=${KEYCLOAK_MCP_CLIENT_SECRET}
EOF
  chmod 600 "$SECRETS/keycloak.env"
else
  set -a
  # shellcheck source=/dev/null
  source "$SECRETS/keycloak.env"
  set +a
fi

if should_materialize "$SECRETS/openbao.env"; then
  printf 'BAO_ADDR=http://openbao:8200\n' >"$SECRETS/openbao.env"
  chmod 600 "$SECRETS/openbao.env"
fi

SEAWEED_ACCESS="$(rand_secret | head -c 20)"
SEAWEED_SECRET="$(rand_secret)"
if should_materialize "$SECRETS/seaweedfs.env"; then
  cat >"$SECRETS/seaweedfs.env" <<EOF
SEAWEEDFS_S3_ACCESS_KEY=${SEAWEED_ACCESS}
SEAWEEDFS_S3_SECRET_KEY=${SEAWEED_SECRET}
SEAWEEDFS_S3_ENDPOINT=http://seaweedfs:8333
EOF
  chmod 600 "$SECRETS/seaweedfs.env"
else
  set -a
  # shellcheck source=/dev/null
  source "$SECRETS/seaweedfs.env"
  set +a
  SEAWEED_ACCESS="${SEAWEEDFS_S3_ACCESS_KEY}"
  SEAWEED_SECRET="${SEAWEEDFS_S3_SECRET_KEY}"
fi

if should_materialize "$SECRETS/core.env"; then
  cat >"$SECRETS/core.env" <<EOF
CORE_ENV=self_host
CORE_DATABASE_URL=postgres://memdot_core:${CORE_DB_PASSWORD}@postgres:5432/memdot
MEMDOT_MIGRATION_DATABASE_URL=postgres://memdot_migrate:${MIGRATE_PASSWORD}@postgres:5432/memdot
MEMDOT_BOOTSTRAP_DATABASE_URL=postgres://memdot:${POSTGRES_PASSWORD}@postgres:5432/memdot
CORE_OBJECT_STORE_ENDPOINT=http://seaweedfs:8333
CORE_OBJECT_STORE_ACCESS_KEY=${SEAWEED_ACCESS}
CORE_OBJECT_STORE_SECRET_KEY=${SEAWEED_SECRET}
CORE_OIDC_ISSUER=${OIDC_ISSUER}
CORE_OIDC_AUDIENCE=memdot-core
CORE_ALLOWED_ORIGINS=${PUBLIC_URL}
CORE_OPENBAO_ADDR=http://openbao:8200
CORE_OPENBAO_TRANSIT_TOKEN_FILE=/run/secrets/openbao_transit_token
CORE_TELEMETRY_EXPORT=off
CORE_OTEL_EXPORTER_OTLP_ENDPOINT=
CORE_SESSION_SIGNING_PEPPER=$(rand_secret)
CORE_TENANT_CONTEXT_SIGNING_KEY=${TENANT_CONTEXT_SIGNING_KEY}
CORE_OIDC_CLIENT_ID=memdot-core
CORE_OIDC_CLIENT_SECRET=${KEYCLOAK_CORE_CLIENT_SECRET}
CORE_OIDC_REDIRECT_URI=https://localhost:8443/api/v1/auth/oidc/callback
EOF
  chmod 600 "$SECRETS/core.env"
fi

if should_materialize "$SECRETS/web.env"; then
  cat >"$SECRETS/web.env" <<EOF
WEB_ENV=self_host
WEB_OIDC_ISSUER=${OIDC_ISSUER}
WEB_OIDC_AUDIENCE=memdot-web
WEB_ALLOWED_ORIGINS=${PUBLIC_URL}
WEB_TELEMETRY_EXPORT=off
WEB_OTEL_EXPORTER_OTLP_ENDPOINT=
EOF
  chmod 600 "$SECRETS/web.env"
fi

if should_materialize "$SECRETS/mcp.env"; then
  cat >"$SECRETS/mcp.env" <<EOF
MCP_ENV=self_host
MCP_OIDC_ISSUER=${OIDC_ISSUER}
MCP_OIDC_DISCOVERY_URL=http://keycloak:8080/realms/memdot
MCP_OIDC_AUDIENCE=memdot-mcp
MCP_ALLOWED_ORIGINS=${PUBLIC_URL}
MCP_TELEMETRY_EXPORT=off
MCP_OTEL_EXPORTER_OTLP_ENDPOINT=
EOF
  chmod 600 "$SECRETS/mcp.env"
fi

if should_materialize "$SECRETS/workers.env"; then
  cat >"$SECRETS/workers.env" <<EOF
WORKERS_ENV=self_host
WORKERS_HATCHET_HOST=hatchet-engine
WORKERS_HATCHET_PORT=7070
WORKERS_TELEMETRY_EXPORT=off
WORKERS_OTEL_EXPORTER_OTLP_ENDPOINT=
EOF
  chmod 600 "$SECRETS/workers.env"
fi

if should_materialize "$SECRETS/model-router.env"; then
  cat >"$SECRETS/model-router.env" <<EOF
MODEL_ROUTER_ENV=self_host
MODEL_ROUTER_TEX_ENABLED=false
MODEL_ROUTER_TELEMETRY_EXPORT=off
MODEL_ROUTER_OTEL_EXPORTER_OTLP_ENDPOINT=
EOF
  chmod 600 "$SECRETS/model-router.env"
fi

REALM_RUNTIME="$SECRETS/realm-memdot.runtime.json"
REALM_TEMPLATE="$CONFIG/keycloak/realm-memdot.json.template"
# Always refresh runtime realm when forcing, or when missing
if should_materialize "$REALM_RUNTIME"; then
  sed \
    -e "s|__MEMDOT_PUBLIC_URL__|${PUBLIC_URL}|g" \
    -e "s|__KEYCLOAK_CORE_CLIENT_SECRET__|${KEYCLOAK_CORE_CLIENT_SECRET}|g" \
    -e "s|__KEYCLOAK_MCP_CLIENT_SECRET__|${KEYCLOAK_MCP_CLIENT_SECRET}|g" \
    "$REALM_TEMPLATE" >"$REALM_RUNTIME"
  chmod 600 "$REALM_RUNTIME"
fi

S3_RUNTIME="$SECRETS/s3.runtime.json"
S3_TEMPLATE="$CONFIG/seaweedfs/s3.json.template"
if should_materialize "$S3_RUNTIME"; then
  sed \
    -e "s|__SEAWEEDFS_S3_ACCESS_KEY__|${SEAWEED_ACCESS}|g" \
    -e "s|__SEAWEEDFS_S3_SECRET_KEY__|${SEAWEED_SECRET}|g" \
    "$S3_TEMPLATE" >"$S3_RUNTIME"
  chmod 600 "$S3_RUNTIME"
fi

if [[ ! -f "$SECRETS/openbao_transit_token" ]]; then
  : >"$SECRETS/openbao_transit_token"
  chmod 600 "$SECRETS/openbao_transit_token"
fi

echo "local_secrets_materialized"
echo "public_url=${PUBLIC_URL}"
echo "oidc_issuer=${OIDC_ISSUER}"
echo "do_not_commit_ignored_material=true"
