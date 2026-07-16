"""Self-host first-operator bootstrap (one-time, auditable, concurrency-safe)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from memdot_core.auth.oidc import OidcClaims
from memdot_domain.ids import new_uuid7
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class BootstrapResult:
    account_id: uuid.UUID
    user_id: uuid.UUID
    actor_id: uuid.UUID
    bootstrap_id: uuid.UUID


class BootstrapReplayError(Exception):
    pass


def operator_bootstrap_exists(session: Session) -> bool:
    return bool(session.execute(text("SELECT memdot_auth_bootstrap_exists()")).scalar())


def complete_operator_bootstrap(session: Session, claims: OidcClaims) -> BootstrapResult:
    if operator_bootstrap_exists(session):
        raise BootstrapReplayError("bootstrap_already_completed")

    account_id = new_uuid7()
    user_id = new_uuid7()
    actor_id = new_uuid7()
    bootstrap_id = new_uuid7()
    try:
        session.execute(
            text(
                """
                SELECT memdot_auth_provision_bootstrap(
                  :account_id, :user_id, :actor_id, :bootstrap_id,
                  :email, :issuer, :subject, :provider
                )
                """
            ),
            {
                "account_id": str(account_id),
                "user_id": str(user_id),
                "actor_id": str(actor_id),
                "bootstrap_id": str(bootstrap_id),
                "email": claims.email,
                "issuer": claims.issuer,
                "subject": claims.subject,
                "provider": claims.provider,
            },
        )
    except DBAPIError as exc:
        if "bootstrap_already_completed" in str(exc.orig):
            raise BootstrapReplayError("bootstrap_already_completed") from exc
        raise

    return BootstrapResult(
        account_id=account_id,
        user_id=user_id,
        actor_id=actor_id,
        bootstrap_id=bootstrap_id,
    )
