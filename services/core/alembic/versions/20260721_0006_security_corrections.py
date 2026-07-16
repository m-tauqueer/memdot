"""Security corrections: attempts, turn payloads, Notion/export/deletion durability."""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "20260721_0006"
down_revision = "20260720_0005"
branch_labels = None
depends_on = None

_SQL_PATH = Path(__file__).with_name("20260721_0006_security_corrections.sql")


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    bind = op.get_bind()
    raw = bind.connection.dbapi_connection
    assert raw is not None
    with raw.cursor() as cur:
        cur.execute(sql)


def downgrade() -> None:
    raise NotImplementedError("Security corrections downgrade is owner-controlled; not automated.")
