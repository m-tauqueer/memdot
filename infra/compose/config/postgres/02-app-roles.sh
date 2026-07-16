#!/usr/bin/env bash
set -euo pipefail

# Create application DB roles on first cluster init.
# Passwords come from db-roles.env mounted into the postgres container env.

: "${POSTGRES_USER:?}"
: "${POSTGRES_DB:?}"
: "${MEMDOT_MIGRATE_PASSWORD:?}"
: "${MEMDOT_CORE_PASSWORD:?}"
: "${MEMDOT_TEST_ADMIN_PASSWORD:?}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_migrate') THEN
    CREATE ROLE memdot_migrate NOINHERIT LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS
      PASSWORD '${MEMDOT_MIGRATE_PASSWORD}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_core') THEN
    CREATE ROLE memdot_core NOINHERIT LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS
      PASSWORD '${MEMDOT_CORE_PASSWORD}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_test_admin') THEN
    CREATE ROLE memdot_test_admin NOINHERIT LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS
      PASSWORD '${MEMDOT_TEST_ADMIN_PASSWORD}';
  END IF;
END
\$\$;
GRANT CONNECT ON DATABASE memdot TO memdot_migrate, memdot_core, memdot_test_admin;
GRANT USAGE, CREATE ON SCHEMA public TO memdot_migrate;
GRANT USAGE ON SCHEMA public TO memdot_core, memdot_test_admin;
EOSQL
