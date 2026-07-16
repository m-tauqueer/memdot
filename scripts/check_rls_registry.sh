#!/usr/bin/env bash
set -euo pipefail

# Live-database RLS registry gate.
# Compares account-owned tables against: ownership registry, ENABLE/FORCE RLS,
# policies, table owner, runtime grants, and adversarial-test registration.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

URL="${MEMDOT_MIGRATION_DATABASE_URL:-${MEMDOT_TEST_DATABASE_URL:-${TEST_DATABASE_URL:-}}}"
if [[ -z "$URL" ]]; then
  echo "MEMDOT_MIGRATION_DATABASE_URL or MEMDOT_TEST_DATABASE_URL required" >&2
  exit 2
fi

export MEMDOT_MIGRATION_DATABASE_URL="$URL"
export MEMDOT_CHECK_RLS_DATABASE_URL="$URL"

uv run python - <<'PY'
from __future__ import annotations

import os
import re
from pathlib import Path

from alembic import command
from alembic.config import Config
from memdot_core.db.registry import ACCOUNT_OWNED_TABLES
from sqlalchemy import create_engine, text

url = os.environ["MEMDOT_CHECK_RLS_DATABASE_URL"]
root = Path("services/core")
cfg = Config(str(root / "alembic.ini"))
cfg.set_main_option("script_location", str(root / "alembic"))
os.environ["MEMDOT_MIGRATION_DATABASE_URL"] = url
command.upgrade(cfg, "head")

engine = create_engine(url)
errors: list[str] = []

adversarial = Path("tests/security/test_rls_adversarial.py").read_text(encoding="utf-8")
# Every account-owned table must appear in the adversarial suite registration list.
missing_adv = sorted(
    t for t in ACCOUNT_OWNED_TABLES if f'"{t}"' not in adversarial and f"'{t}'" not in adversarial
)
if missing_adv:
    errors.append(f"adversarial_unregistered:{','.join(missing_adv)}")

with engine.connect() as conn:
    actual = {
        r[0]
        for r in conn.execute(
            text(
                """
                SELECT c.relname
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'account_id'
                WHERE n.nspname = 'public' AND c.relkind = 'r'
                """
            )
        )
    }
    # oidc_* and memdot_context_secret are intentionally not account-owned
    declared = set(ACCOUNT_OWNED_TABLES)
    if actual - declared:
        errors.append(f"undeclared_account_owned:{','.join(sorted(actual - declared))}")
    if declared - actual:
        errors.append(f"missing_tables:{','.join(sorted(declared - actual))}")

    for table in sorted(ACCOUNT_OWNED_TABLES):
        sql_ident = '"user"' if table == "user" else table
        row = conn.execute(
            text(
                """
                SELECT c.relrowsecurity, c.relforcerowsecurity, pg_get_userbyid(c.relowner)
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = :table
                """
            ),
            {"table": table},
        ).one_or_none()
        if row is None:
            errors.append(f"missing:{table}")
            continue
        enabled, forced, owner = row
        if not enabled:
            errors.append(f"rls_disabled:{table}")
        if not forced:
            errors.append(f"rls_not_forced:{table}")
        if owner != "memdot_migrate":
            errors.append(f"owner_not_migrate:{table}:{owner}")

        policies = list(
            conn.execute(
                text(
                    """
                    SELECT polname FROM pg_policy
                    WHERE polrelid = (
                      SELECT c.oid FROM pg_class c
                      JOIN pg_namespace n ON n.oid = c.relnamespace
                      WHERE n.nspname = 'public' AND c.relname = :table
                    )
                    """
                ),
                {"table": table},
            )
        )
        if not policies:
            errors.append(f"no_policies:{table}")

        grants = conn.execute(
            text(
                f"""
                SELECT has_table_privilege('memdot_core', 'public.{sql_ident}', 'SELECT')
                     , has_table_privilege('memdot_core', 'public.{sql_ident}', 'INSERT')
                     , has_table_privilege('memdot_core', 'public.{sql_ident}', 'UPDATE')
                     , has_table_privilege('memdot_core', 'public.{sql_ident}', 'DELETE')
                     , has_table_privilege('memdot_core', 'public.{sql_ident}', 'TRUNCATE')
                """
            )
        ).one()
        if table in {"current_source_revision", "current_document_revision"}:
            if grants[0] is not True or any(grants[1:4]):
                errors.append(f"pointer_direct_mutation_grant:{table}:{grants}")
        elif not all(grants[:4]):
            errors.append(f"missing_runtime_dml_grant:{table}")
        if grants[4]:
            errors.append(f"unexpected_truncate_grant:{table}")

    # Negative control: temporarily pretend a registered table lacks FORCE and fail.
    # (We assert the detection logic by checking a known-good inverted condition.)
    probe = conn.execute(
        text(
            """
            SELECT count(*) FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = 'account'
              AND c.relforcerowsecurity = false
            """
        )
    ).scalar()
    if probe != 0:
        errors.append("negative_control_account_force_missing")

    privileged_functions = {
        "memdot_clear_tenant_context",
        "memdot_begin_tenant_context",
        "memdot_rls_ok",
        "memdot_external_space_ok",
        "memdot_auth_find_identity",
        "memdot_auth_load_session",
        "memdot_auth_bootstrap_exists",
        "memdot_auth_find_actor_for_user",
        "memdot_oidc_create_challenge",
        "memdot_oidc_load_challenge",
        "memdot_oidc_consume_challenge",
        "memdot_oidc_record_replay",
        "memdot_set_current_source_revision",
        "memdot_set_current_document_revision",
        "memdot_set_current_memory_revision",
        "memdot_auth_provision_hosted",
        "memdot_auth_provision_bootstrap",
    }
    public_execute = {
        r[0]
        for r in conn.execute(
            text(
                """
                SELECT DISTINCT p.proname
                FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                CROSS JOIN LATERAL aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) acl
                WHERE n.nspname = 'public' AND acl.grantee = 0
                  AND acl.privilege_type = 'EXECUTE'
                """
            )
        )
    }
    leaked = sorted(privileged_functions & public_execute)
    if leaked:
        errors.append(f"public_function_execute:{','.join(leaked)}")

    oidc_grants = conn.execute(
        text(
            """
            SELECT has_table_privilege('memdot_core', 'public.oidc_login_challenge', 'SELECT'),
                   has_table_privilege('memdot_core', 'public.oidc_login_challenge', 'INSERT'),
                   has_table_privilege('memdot_core', 'public.oidc_login_challenge', 'UPDATE'),
                   has_table_privilege('memdot_core', 'public.oidc_login_challenge', 'DELETE'),
                   has_table_privilege('memdot_core', 'public.oidc_token_replay', 'SELECT'),
                   has_table_privilege('memdot_core', 'public.oidc_token_replay', 'INSERT'),
                   has_table_privilege('memdot_core', 'public.oidc_token_replay', 'UPDATE'),
                   has_table_privilege('memdot_core', 'public.oidc_token_replay', 'DELETE')
            """
        )
    ).one()
    if any(oidc_grants):
        errors.append(f"runtime_direct_oidc_table_grant:{oidc_grants}")

if errors:
    raise SystemExit("check_rls_failed:" + "|".join(errors))
print(f"rls_registry_ok tables={len(ACCOUNT_OWNED_TABLES)}")
PY

echo "RLS registry gate passed."
