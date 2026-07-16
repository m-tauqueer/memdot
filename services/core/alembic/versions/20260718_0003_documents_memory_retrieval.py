"""Documents, memory, retrieval, and context receipt extensions."""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "20260718_0003"
down_revision = "20260717_0002"
branch_labels = None
depends_on = None

_SQL_PATH = Path(__file__).with_name("20260718_0003_documents_memory_retrieval.sql")


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    bind = op.get_bind()
    raw = bind.connection.dbapi_connection
    assert raw is not None
    with raw.cursor() as cur:
        cur.execute(sql)


def downgrade() -> None:
    raise NotImplementedError("Wave 5 downgrade is owner-controlled; not automated.")
