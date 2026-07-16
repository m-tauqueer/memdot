"""Evidence ledger ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from memdot_domain.tenancy import ConflictResolution, ProposalStatus, TruthClass
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from memdot_core.db.base import Base


class Source(Base):
    __tablename__ = "source"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "space_id"],
            ["space.account_id", "space.id"],
            name="fk_source_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_source_1"),
        UniqueConstraint("account_id", "space_id", "id", name="uq_source_space_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceRevision(Base):
    __tablename__ = "source_revision"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "source_id"],
            ["source.account_id", "source.id"],
            name="fk_source_revision_source",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "source_id"],
            ["source.account_id", "source.space_id", "source.id"],
            name="fk_source_revision_source_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_source_revision_1"),
        UniqueConstraint("account_id", "source_id", "snapshot_sha256", name="uq_source_revision_2"),
        UniqueConstraint("account_id", "space_id", "id", name="uq_source_revision_space_id"),
        UniqueConstraint(
            "account_id",
            "space_id",
            "source_id",
            "id",
            name="uq_source_revision_pointer",
        ),
        CheckConstraint("char_length(snapshot_sha256) = 64", name="ck_source_revision_sha_len"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_native_version: Mapped[str | None] = mapped_column(String(256))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    language_hints: Mapped[str | None] = mapped_column(Text)
    byte_count: Mapped[int | None] = mapped_column(BigInteger)
    page_count: Mapped[int | None] = mapped_column(Integer)
    object_key: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceBlob(Base):
    __tablename__ = "source_blob"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "source_revision_id"],
            ["source_revision.account_id", "source_revision.id"],
            name="fk_source_blob_revision",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "source_revision_id"],
            ["source_revision.account_id", "source_revision.space_id", "source_revision.id"],
            name="fk_source_blob_revision_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_source_blob_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    blob_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthoredDocument(Base):
    __tablename__ = "authored_document"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "space_id"],
            ["space.account_id", "space.id"],
            name="fk_authored_document_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_authored_document_1"),
        UniqueConstraint("account_id", "space_id", "id", name="uq_authored_document_space_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentRevision(Base):
    __tablename__ = "document_revision"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "document_id"],
            ["authored_document.account_id", "authored_document.id"],
            name="fk_document_revision_document",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "document_id"],
            ["authored_document.account_id", "authored_document.space_id", "authored_document.id"],
            name="fk_document_revision_document_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_document_revision_1"),
        UniqueConstraint("account_id", "space_id", "id", name="uq_document_revision_space_id"),
        UniqueConstraint(
            "account_id",
            "space_id",
            "document_id",
            "id",
            name="uq_document_revision_pointer",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    base_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ParseRun(Base):
    __tablename__ = "parse_run"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "source_revision_id"],
            ["source_revision.account_id", "source_revision.id"],
            name="fk_parse_run_revision",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "source_revision_id"],
            ["source_revision.account_id", "source_revision.space_id", "source_revision.id"],
            name="fk_parse_run_revision_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_parse_run_1"),
        UniqueConstraint("account_id", "space_id", "id", name="uq_parse_run_space_id"),
        CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')",
            name="ck_parse_run_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    parser_profile: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    profile_hash: Mapped[str | None] = mapped_column(String(64))
    is_shadow: Mapped[bool] = mapped_column(default=False)
    quality_score: Mapped[float | None] = mapped_column()
    stage_checkpoint: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    artifact_object_key: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_safe: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentElement(Base):
    __tablename__ = "document_element"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "parse_run_id"],
            ["parse_run.account_id", "parse_run.id"],
            name="fk_document_element_parse_run",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "parse_run_id"],
            ["parse_run.account_id", "parse_run.space_id", "parse_run.id"],
            name="fk_document_element_parse_run_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_document_element_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    parse_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    element_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    locator: Mapped[str | None] = mapped_column(Text)
    element_index: Mapped[int | None] = mapped_column(Integer)
    parent_element_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    exact_text: Mapped[str | None] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    element_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProvenanceRecord(Base):
    __tablename__ = "provenance_record"
    __table_args__ = (UniqueConstraint("account_id", "id", name="uq_provenance_record_1"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    activity: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TruthClassification(Base):
    __tablename__ = "truth_classification"
    __table_args__ = (
        UniqueConstraint("account_id", "id", name="uq_truth_classification_1"),
        UniqueConstraint(
            "account_id", "entity_type", "entity_id", name="uq_truth_classification_2"
        ),
        CheckConstraint(
            "truth_class IN ("
            "'source_assertion', 'user_assertion', 'external_knowledge', "
            "'derived_proposal', 'approved_derived', 'learner_evidence', 'system_metadata'"
            ")",
            name="ck_truth_classification_class",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    truth_class: Mapped[str] = mapped_column(
        String(64), nullable=False, default=TruthClass.SOURCE_ASSERTION
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConflictSet(Base):
    __tablename__ = "conflict_set"
    __table_args__ = (
        UniqueConstraint("account_id", "id", name="uq_conflict_set_1"),
        CheckConstraint(
            "resolution IN ('unresolved', 'user_resolved', 'source_superseded')",
            name="ck_conflict_set_resolution",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    resolution: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ConflictResolution.UNRESOLVED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConflictMember(Base):
    __tablename__ = "conflict_member"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "conflict_set_id"],
            ["conflict_set.account_id", "conflict_set.id"],
            name="fk_conflict_member_set",
        ),
        UniqueConstraint("account_id", "id", name="uq_conflict_member_1"),
        UniqueConstraint(
            "account_id", "conflict_set_id", "entity_type", "entity_id", name="uq_conflict_member_2"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    conflict_set_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Proposal(Base):
    __tablename__ = "proposal"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "space_id"],
            ["space.account_id", "space.id"],
            name="fk_proposal_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_proposal_1"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired', 'conflicted')",
            name="ck_proposal_status",
        ),
        CheckConstraint(
            "truth_class = 'derived_proposal'",
            name="ck_proposal_truth_class",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    base_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    truth_class: Mapped[str] = mapped_column(
        String(64), nullable=False, default=TruthClass.DERIVED_PROPOSAL
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ProposalStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversation"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "space_id"],
            ["space.account_id", "space.id"],
            name="fk_conversation_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_conversation_1"),
        UniqueConstraint("account_id", "space_id", "id", name="uq_conversation_space_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_client: Mapped[str] = mapped_column(String(64), nullable=False)
    completeness: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConversationTurn(Base):
    __tablename__ = "conversation_turn"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "conversation_id"],
            ["conversation.account_id", "conversation.id"],
            name="fk_conversation_turn_conversation",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "conversation_id"],
            ["conversation.account_id", "conversation.space_id", "conversation.id"],
            name="fk_conversation_turn_conversation_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_conversation_turn_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_event"
    __table_args__ = (UniqueConstraint("account_id", "id", name="uq_audit_event_1"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CurrentSourceRevision(Base):
    __tablename__ = "current_source_revision"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "source_id"],
            ["source.account_id", "source.id"],
            name="fk_current_source_revision_source",
        ),
        ForeignKeyConstraint(
            ["account_id", "revision_id"],
            ["source_revision.account_id", "source_revision.id"],
            name="fk_current_source_revision_revision",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "source_id", "revision_id"],
            [
                "source_revision.account_id",
                "source_revision.space_id",
                "source_revision.source_id",
                "source_revision.id",
            ],
            name="fk_current_source_revision_same_source",
        ),
        UniqueConstraint("account_id", "source_id", name="uq_current_source_revision_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CurrentDocumentRevision(Base):
    __tablename__ = "current_document_revision"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "document_id"],
            ["authored_document.account_id", "authored_document.id"],
            name="fk_current_document_revision_document",
        ),
        ForeignKeyConstraint(
            ["account_id", "revision_id"],
            ["document_revision.account_id", "document_revision.id"],
            name="fk_current_document_revision_revision",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "document_id", "revision_id"],
            [
                "document_revision.account_id",
                "document_revision.space_id",
                "document_revision.document_id",
                "document_revision.id",
            ],
            name="fk_current_document_revision_same_document",
        ),
        UniqueConstraint("account_id", "document_id", name="uq_current_document_revision_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OutboxEvent(Base):
    __tablename__ = "outbox_event"
    __table_args__ = (UniqueConstraint("account_id", "id", name="uq_outbox_event_1"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    claim_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    claim_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    claimed_by: Mapped[str | None] = mapped_column(Text)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_record"
    __table_args__ = (
        UniqueConstraint("account_id", "idempotency_key", name="uq_idempotency_record_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    fingerprint_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    route: Mapped[str | None] = mapped_column(Text)
    response_body: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    response_headers: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DurableJob(Base):
    __tablename__ = "durable_job"
    __table_args__ = (
        UniqueConstraint("account_id", "id", name="uq_durable_job_1"),
        CheckConstraint(
            "status IN ("
            "'pending', 'queued', 'running', 'succeeded', 'failed', 'cancelled', 'dead_letter'"
            ")",
            name="ck_durable_job_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    job_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    space_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(256))
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    progress: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_safe: Mapped[str | None] = mapped_column(Text)
    auth_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dead_letter_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobAttempt(Base):
    __tablename__ = "job_attempt"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "job_id"],
            ["durable_job.account_id", "durable_job.id"],
            name="fk_job_attempt_job",
        ),
        UniqueConstraint("account_id", "id", name="uq_job_attempt_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_safe: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectionState(Base):
    __tablename__ = "projection_state"
    __table_args__ = (
        UniqueConstraint("account_id", "projection_name", name="uq_projection_state_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    projection_name: Mapped[str] = mapped_column(String(128), nullable=False)
    cursor: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UploadIntent(Base):
    __tablename__ = "upload_intent"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "source_id"],
            ["source.account_id", "source.id"],
            name="fk_upload_intent_source",
        ),
        ForeignKeyConstraint(
            ["account_id", "space_id", "source_id"],
            ["source.account_id", "source.space_id", "source.id"],
            name="fk_upload_intent_source_space",
        ),
        UniqueConstraint("account_id", "id", name="uq_upload_intent_1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    expected_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_byte_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CurrentActiveParseRun(Base):
    __tablename__ = "current_active_parse_run"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "source_id"],
            ["source.account_id", "source.id"],
            name="fk_current_active_parse_source",
        ),
        ForeignKeyConstraint(
            ["account_id", "source_revision_id"],
            ["source_revision.account_id", "source_revision.id"],
            name="fk_current_active_parse_revision",
        ),
        ForeignKeyConstraint(
            ["account_id", "parse_run_id"],
            ["parse_run.account_id", "parse_run.id"],
            name="fk_current_active_parse_run",
        ),
        UniqueConstraint(
            "account_id", "source_id", "source_revision_id", name="uq_current_active_parse_run_1"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    parse_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
