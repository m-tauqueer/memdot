"""Learning curriculum, assessments, learner events, and scheduling projections."""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "20260719_0004"
down_revision = "20260718_0003"
branch_labels = None
depends_on = None

_SQL_PATH = Path(__file__).with_name("20260719_0004_learning.sql")


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    bind = op.get_bind()
    raw = bind.connection.dbapi_connection
    assert raw is not None
    with raw.cursor() as cur:
        cur.execute(sql)


def downgrade() -> None:
    raise NotImplementedError("Learning downgrade is owner-controlled; not automated.")
