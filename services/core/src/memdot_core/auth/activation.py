"""Hosted activation and identity linkage services."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from memdot_core.auth.oidc import OidcClaims
from memdot_core.db.models.tenancy import Account, HostedAdultAttestation
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import AccountStatus
from sqlalchemy import select, text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class IdentityLinkResult:
    account_id: uuid.UUID
    user_id: uuid.UUID
    actor_id: uuid.UUID
    created: bool


class AttestationRequiredError(Exception):
    pass


class AttestationDeclinedError(Exception):
    pass


def link_or_create_hosted_identity(session: Session, claims: OidcClaims) -> IdentityLinkResult:
    existing = (
        session.execute(
            text(
                "SELECT id, account_id, user_id FROM memdot_auth_find_identity(:issuer, :subject)"
            ),
            {"issuer": claims.issuer, "subject": claims.subject},
        )
        .mappings()
        .first()
    )
    if existing is not None:
        actor = (
            session.execute(
                text("SELECT id FROM memdot_auth_find_actor_for_user(:account_id, :user_id)"),
                {
                    "account_id": str(existing["account_id"]),
                    "user_id": str(existing["user_id"]),
                },
            )
            .mappings()
            .first()
        )
        if actor is None:
            msg = "actor_missing_for_identity"
            raise RuntimeError(msg)
        return IdentityLinkResult(
            account_id=existing["account_id"],
            user_id=existing["user_id"],
            actor_id=actor["id"],
            created=False,
        )

    account_id = new_uuid7()
    user_id = new_uuid7()
    actor_id = new_uuid7()
    session.execute(
        text(
            """
            SELECT memdot_auth_provision_hosted(
              :account_id, :user_id, :actor_id, :email, :issuer, :subject, :provider
            )
            """
        ),
        {
            "account_id": str(account_id),
            "user_id": str(user_id),
            "actor_id": str(actor_id),
            "email": claims.email,
            "issuer": claims.issuer,
            "subject": claims.subject,
            "provider": claims.provider or "google",
        },
    )
    return IdentityLinkResult(
        account_id=account_id,
        user_id=user_id,
        actor_id=actor_id,
        created=True,
    )


def record_adult_attestation(
    session: Session,
    *,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    confirmed: bool,
) -> None:
    if not confirmed:
        raise AttestationDeclinedError("attestation_declined")
    account = session.get(Account, account_id)
    if account is None:
        raise AttestationRequiredError("account_missing")
    existing = session.execute(
        select(HostedAdultAttestation).where(
            HostedAdultAttestation.account_id == account_id,
            HostedAdultAttestation.user_id == user_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        # Confirmation is canonical account state, not a one-time browser action.
        account.status = AccountStatus.ACTIVE
        return
    session.add(
        HostedAdultAttestation(
            id=new_uuid7(),
            account_id=account_id,
            user_id=user_id,
            confirmed=True,
        )
    )
    account.status = AccountStatus.ACTIVE
