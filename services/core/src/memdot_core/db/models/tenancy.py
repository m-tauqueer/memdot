"""Tenancy and identity ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from memdot_domain.tenancy import AccountStatus, ActorKind, MemberRole, SpaceVisibility
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from memdot_core.db.base import Base


class Account(Base):
    __tablename__ = "account"
    __table_args__ = (
        UniqueConstraint("account_id", "id", name="uq_account_1"),
        CheckConstraint(
            "status IN ('pending_attestation', 'active', 'disabled')",
            name="ck_account_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AccountStatus.PENDING_ATTESTATION
    )
    display_name: Mapped[str | None] = mapped_column(String(256))
    timezone: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_user_account"),
        UniqueConstraint("account_id", "id", name="uq_user_1"),
        {"quote": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    display_name: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AccountMember(Base):
    __tablename__ = "account_member"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_account_member_account"),
        ForeignKeyConstraint(
            ["account_id", "user_id"],
            ["user.account_id", "user.id"],
            name="fk_account_member_user",
        ),
        UniqueConstraint("account_id", "id", name="uq_account_member_1"),
        UniqueConstraint("account_id", "user_id", name="uq_account_member_2"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=MemberRole.OWNER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Space(Base):
    __tablename__ = "space"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_space_account"),
        UniqueConstraint("account_id", "id", name="uq_space_1"),
        CheckConstraint(
            "visibility IN ('general', 'learning', 'private')",
            name="ck_space_visibility",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SpaceVisibility.GENERAL
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SpaceMember(Base):
    __tablename__ = "space_member"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "space_id"],
            ["space.account_id", "space.id"],
            name="fk_space_member_space",
        ),
        ForeignKeyConstraint(
            ["account_id", "user_id"],
            ["user.account_id", "user.id"],
            name="fk_space_member_user",
        ),
        UniqueConstraint("account_id", "space_id", "user_id", name="uq_space_member_1"),
        UniqueConstraint("account_id", "id", name="uq_space_member_2"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=MemberRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HostedAdultAttestation(Base):
    __tablename__ = "hosted_adult_attestation"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_attestation_account"),
        ForeignKeyConstraint(
            ["account_id", "user_id"],
            ["user.account_id", "user.id"],
            name="fk_attestation_user",
        ),
        UniqueConstraint("account_id", "user_id", name="uq_hosted_adult_attestation_1"),
        UniqueConstraint("account_id", "id", name="uq_hosted_adult_attestation_2"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ExternalIdentity(Base):
    __tablename__ = "external_identity"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_external_identity_account"),
        ForeignKeyConstraint(
            ["account_id", "user_id"],
            ["user.account_id", "user.id"],
            name="fk_external_identity_user",
        ),
        UniqueConstraint("issuer", "subject", name="uq_external_identity_1"),
        UniqueConstraint("account_id", "id", name="uq_external_identity_2"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    issuer: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Actor(Base):
    __tablename__ = "actor"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_actor_account"),
        UniqueConstraint("account_id", "id", name="uq_actor_1"),
        CheckConstraint(
            "kind IN ('user', 'external_client', 'system')",
            name="ck_actor_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default=ActorKind.USER)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BrowserSession(Base):
    __tablename__ = "browser_session"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_browser_session_account"),
        ForeignKeyConstraint(
            ["account_id", "user_id"],
            ["user.account_id", "user.id"],
            name="fk_browser_session_user",
        ),
        ForeignKeyConstraint(
            ["account_id", "actor_id"],
            ["actor.account_id", "actor.id"],
            name="fk_browser_session_actor",
        ),
        UniqueConstraint("account_id", "id", name="uq_browser_session_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    csrf_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_auth_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionRevocation(Base):
    __tablename__ = "session_revocation"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "session_id"],
            ["browser_session.account_id", "browser_session.id"],
            name="fk_session_revocation_session",
        ),
        UniqueConstraint("account_id", "id", name="uq_session_revocation_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExternalClientGrant(Base):
    __tablename__ = "external_client_grant"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_external_grant_account"),
        ForeignKeyConstraint(
            ["account_id", "actor_id"],
            ["actor.account_id", "actor.id"],
            name="fk_external_grant_actor",
        ),
        UniqueConstraint("account_id", "id", name="uq_external_client_grant_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    client_id: Mapped[str] = mapped_column(String(256), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OperatorBootstrap(Base):
    __tablename__ = "operator_bootstrap"
    __table_args__ = (
        ForeignKeyConstraint(["account_id"], ["account.id"], name="fk_operator_bootstrap_account"),
        UniqueConstraint("account_id", "id", name="uq_operator_bootstrap_1"),
        UniqueConstraint("singleton_key", name="uq_operator_bootstrap_singleton"),
        CheckConstraint("singleton_key = 1", name="ck_operator_bootstrap_singleton"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    issuer: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    singleton_key: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OidcLoginChallenge(Base):
    """Server-issued OIDC state/nonce (hashed, expiring, single-use)."""

    __tablename__ = "oidc_login_challenge"
    __table_args__ = (UniqueConstraint("state_hash", name="uq_oidc_login_challenge_state"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    state_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    nonce_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    pkce_verifier_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OidcTokenReplay(Base):
    """Durable OIDC jti replay prevention."""

    __tablename__ = "oidc_token_replay"
    __table_args__ = (UniqueConstraint("issuer", "jti", name="uq_oidc_token_replay_1"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    issuer: Mapped[str] = mapped_column(Text, nullable=False)
    jti: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
