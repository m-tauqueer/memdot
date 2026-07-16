"""Resolve external_client_grant via SECURITY DEFINER — never trust edge claims alone."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from memdot_core.auth.bearer import BearerValidationError, parse_scopes
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ResolvedExternalGrant:
    grant_id: uuid.UUID
    account_id: uuid.UUID
    actor_id: uuid.UUID
    client_id: str
    scopes: frozenset[str]


def resolve_external_grant(
    db: Session,
    *,
    client_id: str,
    account_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    token_scopes: frozenset[str],
) -> ResolvedExternalGrant:
    """Look up the current grant and intersect scopes with the token."""
    if not client_id.strip():
        raise BearerValidationError("missing_client")
    rows = (
        db.execute(
            text(
                """
            SELECT grant_id, account_id, actor_id, client_id, scopes, revoked_at
            FROM memdot_resolve_external_grant(:client_id, :account_id, :actor_id)
            """
            ),
            {
                "client_id": client_id,
                "account_id": account_id,
                "actor_id": actor_id,
            },
        )
        .mappings()
        .all()
    )
    if len(rows) != 1:
        raise BearerValidationError("grant_not_found")
    row = rows[0]
    if row["revoked_at"] is not None:
        raise BearerValidationError("grant_revoked")
    grant_scopes = frozenset(parse_scopes(row["scopes"]))
    effective: frozenset[str] = token_scopes & grant_scopes if grant_scopes else frozenset()
    if not effective:
        raise BearerValidationError("scope_mismatch")
    # Token must not claim broader authority than the grant after intersection;
    # any token scope outside the grant is dropped; require purpose-relevant scope remains.
    return ResolvedExternalGrant(
        grant_id=uuid.UUID(str(row["grant_id"])),
        account_id=uuid.UUID(str(row["account_id"])),
        actor_id=uuid.UUID(str(row["actor_id"])),
        client_id=str(row["client_id"]),
        scopes=effective,
    )
