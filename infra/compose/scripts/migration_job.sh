#!/usr/bin/env bash
set -euo pipefail

# Bounded domain migration job (Phase 3+). Never runs during app startup.
# Fails non-zero when required migration config is absent (no skipped success).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRETS="${MEMDOT_SECRETS_DIR:-$COMPOSE_DIR/secrets}"
MODE="${1:-self_host}"

case "$MODE" in
  hosted|self_host|test|development) ;;
  *)
    echo "invalid mode: $MODE" >&2
    exit 2
    ;;
esac

if [[ -f "$SECRETS/db-roles.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$SECRETS/db-roles.env"
  set +a
fi
if [[ -f "$SECRETS/core.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$SECRETS/core.env"
  set +a
fi

# Allow callers (selfhost smoke) to override URLs for published host ports.
if [[ -n "${MEMDOT_MIGRATION_DATABASE_URL_OVERRIDE:-}" ]]; then
  export MEMDOT_MIGRATION_DATABASE_URL="$MEMDOT_MIGRATION_DATABASE_URL_OVERRIDE"
fi
if [[ -n "${MEMDOT_BOOTSTRAP_DATABASE_URL_OVERRIDE:-}" ]]; then
  export MEMDOT_BOOTSTRAP_DATABASE_URL="$MEMDOT_BOOTSTRAP_DATABASE_URL_OVERRIDE"
fi

if [[ -z "${MEMDOT_MIGRATION_DATABASE_URL:-}" ]]; then
  echo "MEMDOT_MIGRATION_DATABASE_URL is required for migration_job" >&2
  exit 2
fi

# Ensure roles exist / passwords match materialized secrets when Compose secrets present.
if [[ -f "$SECRETS/postgres.env" && -f "$SECRETS/db-roles.env" ]]; then
  # Prefer in-compose postgres hostname when CORE URL uses it.
  if [[ "${MEMDOT_MIGRATION_DATABASE_URL}" == *"@postgres:"* ]]; then
    export MEMDOT_PG_HOST="${MEMDOT_PG_HOST:-postgres}"
    export MEMDOT_PG_PORT="${MEMDOT_PG_PORT:-5432}"
  fi
  # When running on the host against published port, callers set MEMDOT_PG_HOST.
  if [[ -n "${MEMDOT_BOOTSTRAP_DATABASE_URL:-}" ]] || [[ -n "${MEMDOT_PG_HOST:-}" ]]; then
    bash "$COMPOSE_DIR/scripts/ensure_db_roles.sh"
  fi
fi

export MEMDOT_MIGRATION_DATABASE_URL
bash "$ROOT/scripts/migrate_domain.sh"

# Verify Alembic head + expected schema (not a skipped placeholder).
HEAD="$(cd "$ROOT/services/core" && uv run alembic current 2>/dev/null | tail -n 1 || true)"
if [[ "$HEAD" != *"20260716_0001"* ]]; then
  echo "alembic_head_mismatch: $HEAD" >&2
  exit 1
fi

python_check="$(
  cd "$ROOT" && uv run python - <<'PY'
import os
from sqlalchemy import create_engine, text

def normalize(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url

url = normalize(os.environ["MEMDOT_MIGRATION_DATABASE_URL"])
engine = create_engine(url)
required = {"account", "space", "source", "browser_session", "alembic_version"}
with engine.connect() as conn:
    tables = {r[0] for r in conn.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    ))}
    missing = sorted(required - tables)
    if missing:
        raise SystemExit(f"schema_missing:{','.join(missing)}")
    ver = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    if ver != "20260716_0001":
        raise SystemExit(f"alembic_version_mismatch:{ver}")
print("schema_ok")
PY
)"
echo "mode=$MODE"
echo "action=alembic_upgrade_head"
echo "head=20260716_0001"
echo "$python_check"
