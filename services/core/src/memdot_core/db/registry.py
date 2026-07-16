"""Registry of account-owned tables requiring FORCE RLS and adversarial coverage."""

from __future__ import annotations

ACCOUNT_OWNED_TABLES: frozenset[str] = frozenset(
    {
        # Tenancy and identity (3.1)
        "account",
        "user",
        "account_member",
        "space",
        "space_member",
        "hosted_adult_attestation",
        "external_identity",
        "actor",
        "browser_session",
        "session_revocation",
        "external_client_grant",
        "operator_bootstrap",
        # Evidence ledger (3.2)
        "source",
        "source_revision",
        "source_blob",
        "authored_document",
        "document_revision",
        "parse_run",
        "document_element",
        "provenance_record",
        "truth_classification",
        "conflict_set",
        "conflict_member",
        "proposal",
        "conversation",
        "conversation_turn",
        "audit_event",
        "current_source_revision",
        "current_document_revision",
        "outbox_event",
        "idempotency_record",
        "durable_job",
        "job_attempt",
        "projection_state",
    }
)

IMMUTABLE_TABLES: frozenset[str] = frozenset(
    {
        "source_revision",
        "document_revision",
        "audit_event",
        "conversation_turn",
        "job_attempt",
    }
)

APPEND_ONLY_TABLES: frozenset[str] = frozenset(
    {
        "audit_event",
        "conversation_turn",
        "outbox_event",
        "job_attempt",
    }
)

MUTABLE_POINTER_TABLES: frozenset[str] = frozenset(
    {
        "current_source_revision",
        "current_document_revision",
    }
)
