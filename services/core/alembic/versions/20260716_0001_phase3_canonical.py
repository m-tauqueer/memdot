"""Phase 3 tenancy, ledger, roles, protected context, RLS, and integrity triggers."""

from __future__ import annotations

import os
from pathlib import Path

from alembic import op
from sqlalchemy import text

revision = "20260716_0001"
down_revision = None
branch_labels = None
depends_on = None

_SQL_PATH = Path(__file__).with_name("20260716_0001_phase3_canonical.sql")


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    # Split on statement boundaries carefully: execute as a single script via psycopg
    # using connection.execute for the whole file (PostgreSQL accepts multi-statement).
    bind = op.get_bind()
    # Use raw DBAPI connection for multi-statement SQL script.
    raw = bind.connection.dbapi_connection
    assert raw is not None
    with raw.cursor() as cur:
        cur.execute(sql)
    signing_key = os.environ.get("MEMDOT_TENANT_CONTEXT_SIGNING_KEY") or os.environ.get(
        "CORE_TENANT_CONTEXT_SIGNING_KEY"
    )
    if signing_key is None or len(signing_key) < 32:
        raise RuntimeError(
            "MEMDOT_TENANT_CONTEXT_SIGNING_KEY or CORE_TENANT_CONTEXT_SIGNING_KEY "
            "must contain at least 32 characters"
        )
    bind.execute(
        text("UPDATE memdot_context_secret SET hmac_key = :key WHERE id = 1"),
        {"key": signing_key.encode("utf-8")},
    )


def downgrade() -> None:
    raise NotImplementedError("Phase 3 downgrade is owner-controlled; not automated.")
