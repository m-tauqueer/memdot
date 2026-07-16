"""Phase 4 runtime: outbox claiming, durable jobs, ingestion, active parse pointer."""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "20260717_0002"
down_revision = "20260716_0001"
branch_labels = None
depends_on = None

_SQL_PATH = Path(__file__).with_name("20260717_0002_phase4_runtime.sql")


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    bind = op.get_bind()
    raw = bind.connection.dbapi_connection
    assert raw is not None
    with raw.cursor() as cur:
        cur.execute(sql)


def downgrade() -> None:
    raise NotImplementedError("Phase 4 downgrade is owner-controlled; not automated.")
