"""Tenancy, authorization purpose, and truth-class domain types."""

from enum import StrEnum


class AccountStatus(StrEnum):
    PENDING_ATTESTATION = "pending_attestation"
    ACTIVE = "active"
    DISABLED = "disabled"


class SpaceVisibility(StrEnum):
    GENERAL = "general"
    LEARNING = "learning"
    PRIVATE = "private"


class MemberRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class ActorKind(StrEnum):
    USER = "user"
    EXTERNAL_CLIENT = "external_client"
    SYSTEM = "system"


class RequestPurpose(StrEnum):
    FIRST_PARTY = "first_party"
    EXTERNAL_READ = "external_read"
    EXTERNAL_PROPOSE = "external_propose"
    EXTERNAL_INTERACTION = "external_interaction"
    WORKER = "worker"
    MIGRATION = "migration"
    ADMIN = "admin"


class TruthClass(StrEnum):
    SOURCE_ASSERTION = "source_assertion"
    USER_ASSERTION = "user_assertion"
    EXTERNAL_KNOWLEDGE = "external_knowledge"
    DERIVED_PROPOSAL = "derived_proposal"
    APPROVED_DERIVED = "approved_derived"
    LEARNER_EVIDENCE = "learner_evidence"
    SYSTEM_METADATA = "system_metadata"


class ConflictResolution(StrEnum):
    UNRESOLVED = "unresolved"
    USER_RESOLVED = "user_resolved"
    SOURCE_SUPERSEDED = "source_superseded"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONFLICTED = "conflicted"
