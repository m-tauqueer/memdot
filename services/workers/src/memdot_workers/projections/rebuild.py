"""Projection rebuild helpers for local lexical surfaces."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Protocol

from memdot_domain.ids import new_uuid7


def payload_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ProjectionUpsertSession(Protocol):
    def execute(self, statement: object, params: dict[str, object] | None = None) -> object: ...


def upsert_local_lexical_projection(
    session: ProjectionUpsertSession,
    *,
    account_id: uuid.UUID,
    space_id: uuid.UUID,
    canonical_type: str,
    canonical_id: uuid.UUID,
    canonical_revision_id: uuid.UUID,
    text: str,
    provider: str = "local",
    surface: str = "lexical",
    profile_version: str = "v1",
) -> uuid.UUID:
    """Idempotent projection upsert keyed by canonical identity."""
    digest = payload_hash(text)
    projection_id = new_uuid7()
    now = datetime.now(UTC)
    session.execute(
        """
        INSERT INTO projection (
          id, account_id, space_id, provider, surface, profile_version,
          canonical_type, canonical_id, canonical_revision_id,
          provider_document_id, payload_hash, status, indexed_at
        ) VALUES (
          :id, :account_id, :space_id, :provider, :surface, :profile_version,
          :canonical_type, :canonical_id, :canonical_revision_id,
          :provider_document_id, :payload_hash, 'active', :indexed_at
        )
        ON CONFLICT (
          account_id, provider, surface, canonical_type, canonical_id, canonical_revision_id
        )
        DO UPDATE SET
          payload_hash = EXCLUDED.payload_hash,
          status = 'active',
          indexed_at = EXCLUDED.indexed_at,
          tombstoned_at = NULL
        """,
        {
            "id": projection_id,
            "account_id": account_id,
            "space_id": space_id,
            "provider": provider,
            "surface": surface,
            "profile_version": profile_version,
            "canonical_type": canonical_type,
            "canonical_id": canonical_id,
            "canonical_revision_id": canonical_revision_id,
            "provider_document_id": f"{canonical_type}:{canonical_id}",
            "payload_hash": digest,
            "indexed_at": now,
        },
    )
    return projection_id
