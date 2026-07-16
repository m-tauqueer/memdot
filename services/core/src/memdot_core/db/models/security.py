"""Non-tenant security tables (durable nonces, etc.)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from memdot_core.db.base import Base


class ServiceAuthNonce(Base):
    __tablename__ = "service_auth_nonce"
    __table_args__ = (Index("ix_service_auth_nonce_expires", "expires_at"),)

    nonce_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
