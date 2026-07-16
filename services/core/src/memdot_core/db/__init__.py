"""Database package — import model modules so metadata is populated."""

from __future__ import annotations

from memdot_core.db.models import ledger, security, tenancy

# Touch modules so Alembic/autogenerate and Base.metadata see all tables.
_MODEL_MODULES = (ledger, security, tenancy)

__all__ = ["ledger", "security", "tenancy"]
