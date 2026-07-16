-- Create logical databases for Memdot platform services on the shared pgvector instance.
-- Credentials are supplied via POSTGRES_USER / POSTGRES_PASSWORD from operator secrets.
-- memdot_ops holds isolated operational durability fixtures only (no product schema).

SELECT 'CREATE DATABASE hatchet'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hatchet')\gexec

SELECT 'CREATE DATABASE keycloak'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec

SELECT 'CREATE DATABASE memdot_ops'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'memdot_ops')\gexec

\c memdot
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c memdot_ops
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS ops_durability_fixture (
  id text PRIMARY KEY,
  payload text NOT NULL,
  checksum text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Hatchet canary durable effects (unique idempotency_key = one committed effect).
CREATE TABLE IF NOT EXISTS ops_canary_effect (
  idempotency_key text PRIMARY KEY,
  effect_token text NOT NULL,
  workflow_run_id text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops_canary_barrier (
  barrier_id text PRIMARY KEY,
  released boolean NOT NULL DEFAULT false,
  started boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
