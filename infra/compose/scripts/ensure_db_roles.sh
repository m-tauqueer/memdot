#!/usr/bin/env bash
set -euo pipefail

# Idempotent role provisioning for memdot_migrate / memdot_core / memdot_test_admin.
# Uses the PostgreSQL bootstrap superuser from postgres.env. Never prints passwords.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRETS="${MEMDOT_SECRETS_DIR:-$COMPOSE_DIR/secrets}"

if [[ ! -f "$SECRETS/postgres.env" ]]; then
  echo "missing $SECRETS/postgres.env" >&2
  exit 2
fi
if [[ ! -f "$SECRETS/db-roles.env" ]]; then
  echo "missing $SECRETS/db-roles.env" >&2
  exit 2
fi

set -a
# shellcheck disable=SC1091
source "$SECRETS/postgres.env"
# shellcheck disable=SC1091
source "$SECRETS/db-roles.env"
set +a

if [[ -n "${MEMDOT_BOOTSTRAP_DATABASE_URL_OVERRIDE:-}" ]]; then
  MEMDOT_BOOTSTRAP_DATABASE_URL="$MEMDOT_BOOTSTRAP_DATABASE_URL_OVERRIDE"
fi

: "${POSTGRES_USER:?}"
: "${POSTGRES_PASSWORD:?}"
: "${MEMDOT_MIGRATE_PASSWORD:?}"
: "${MEMDOT_CORE_PASSWORD:?}"
: "${MEMDOT_TEST_ADMIN_PASSWORD:?}"

BOOTSTRAP_URL="${MEMDOT_BOOTSTRAP_DATABASE_URL:-postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${MEMDOT_PG_HOST:-127.0.0.1}:${MEMDOT_PG_PORT:-5432}/memdot}"

export PGPASSWORD="$POSTGRES_PASSWORD"
psql "$BOOTSTRAP_URL" -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_migrate') THEN
    CREATE ROLE memdot_migrate NOINHERIT LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS
      PASSWORD '${MEMDOT_MIGRATE_PASSWORD}';
  ELSE
    ALTER ROLE memdot_migrate WITH LOGIN BYPASSRLS PASSWORD '${MEMDOT_MIGRATE_PASSWORD}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_core') THEN
    CREATE ROLE memdot_core NOINHERIT LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS
      PASSWORD '${MEMDOT_CORE_PASSWORD}';
  ELSE
    ALTER ROLE memdot_core WITH LOGIN NOBYPASSRLS PASSWORD '${MEMDOT_CORE_PASSWORD}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_test_admin') THEN
    CREATE ROLE memdot_test_admin NOINHERIT LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS
      PASSWORD '${MEMDOT_TEST_ADMIN_PASSWORD}';
  ELSE
    ALTER ROLE memdot_test_admin WITH LOGIN NOBYPASSRLS PASSWORD '${MEMDOT_TEST_ADMIN_PASSWORD}';
  END IF;
END
\$\$;
GRANT CONNECT ON DATABASE memdot TO memdot_migrate, memdot_core, memdot_test_admin;
GRANT USAGE, CREATE ON SCHEMA public TO memdot_migrate;
GRANT USAGE ON SCHEMA public TO memdot_core, memdot_test_admin;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SQL

echo "db_roles=ok"
