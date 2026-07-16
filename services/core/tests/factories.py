"""Test factories for accounts, spaces, actors, and ledger objects."""
# ruff: noqa: E501 -- compact SQL fixtures mirror the frozen schema columns.

from __future__ import annotations

import uuid
from dataclasses import dataclass

from memdot_core.db.models.ledger import Source
from memdot_core.db.models.tenancy import Account, AccountMember, Actor, Space, User
from memdot_core.db.tenant import TenantContext, reset_tenant_context, tenant_scope
from memdot_domain.ids import deterministic_uuid5, new_uuid7
from memdot_domain.tenancy import (
    AccountStatus,
    ActorKind,
    MemberRole,
    RequestPurpose,
    SpaceVisibility,
)
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class AccountBundle:
    account_id: uuid.UUID
    user_id: uuid.UUID
    actor_id: uuid.UUID


def create_account_bundle(
    session: Session,
    *,
    status: AccountStatus = AccountStatus.ACTIVE,
    visibility: SpaceVisibility = SpaceVisibility.GENERAL,
    private: bool = False,
) -> tuple[AccountBundle, uuid.UUID]:
    """Provision tenancy rows as the bootstrap/test connection (RLS bypass).

    Product writes under memdot_core must use protected ``tenant_scope`` afterwards.
    """
    account_id = new_uuid7()
    user_id = new_uuid7()
    actor_id = new_uuid7()
    space_id = new_uuid7()
    vis = SpaceVisibility.PRIVATE if private else visibility
    session.add(Account(id=account_id, account_id=account_id, status=status.value))
    session.flush()
    session.add(User(id=user_id, account_id=account_id, email="user@example.com"))
    session.flush()
    session.add(
        AccountMember(
            id=new_uuid7(),
            account_id=account_id,
            user_id=user_id,
            role=MemberRole.OWNER.value,
        )
    )
    session.flush()
    session.add(
        Actor(id=actor_id, account_id=account_id, kind=ActorKind.USER.value, reference_id=user_id)
    )
    session.flush()
    session.add(
        Space(
            id=space_id,
            account_id=account_id,
            name="Primary",
            visibility=vis.value,
        )
    )
    session.flush()
    return AccountBundle(account_id=account_id, user_id=user_id, actor_id=actor_id), space_id


def create_source(
    session: Session,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    space_id: uuid.UUID,
    title: str = "Source",
) -> uuid.UUID:
    source_id = new_uuid7()
    ctx = TenantContext(
        account_id=account_id, actor_id=actor_id, purpose=RequestPurpose.FIRST_PARTY
    )
    with tenant_scope(session, ctx):
        session.add(
            Source(
                id=source_id,
                account_id=account_id,
                space_id=space_id,
                title=title,
            )
        )
    reset_tenant_context(session)
    return source_id


def seed_account_owned_graph(
    session: Session, bundle: AccountBundle, space_id: uuid.UUID
) -> dict[str, uuid.UUID]:
    """Seed one connected row in every account-owned table for RLS probes."""
    ids = {
        table: new_uuid7()
        for table in (
            "space_member",
            "hosted_adult_attestation",
            "external_identity",
            "browser_session",
            "session_revocation",
            "external_client_grant",
            "operator_bootstrap",
            "source",
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
            "document_outbox_event",
            "idempotency_record",
            "durable_job",
            "job_attempt",
            "projection_state",
        )
    }
    ids["source_revision"] = deterministic_uuid5(ids["source"], "a" * 64)
    ids["actor_external"] = new_uuid7()

    member_id = session.execute(
        text("SELECT id FROM account_member WHERE account_id=:account_id"),
        {"account_id": bundle.account_id},
    ).scalar_one()
    params = {
        **ids,
        "account_id": bundle.account_id,
        "user_id": bundle.user_id,
        "actor_id": bundle.actor_id,
        "space_id": space_id,
    }
    statements = """
        INSERT INTO space_member VALUES (:space_member,:account_id,:space_id,:user_id,'owner',now());
        INSERT INTO hosted_adult_attestation VALUES (:hosted_adult_attestation,:account_id,:user_id,true,now());
        INSERT INTO external_identity VALUES (:external_identity,:account_id,:user_id,'https://seed.example',CAST(:account_id AS text),'google',now());
        INSERT INTO actor(id,account_id,kind) VALUES (:actor_external,:account_id,'external_client');
        INSERT INTO browser_session(id,account_id,user_id,actor_id,secret_hash,csrf_token_hash,expires_at,idle_expires_at,last_auth_at)
          VALUES (:browser_session,:account_id,:user_id,:actor_id,'secret','csrf',now()+interval '1 hour',now()+interval '1 hour',now());
        INSERT INTO session_revocation VALUES (:session_revocation,:account_id,:browser_session,now());
        INSERT INTO external_client_grant(id,account_id,actor_id,client_id,scopes)
          VALUES (:external_client_grant,:account_id,:actor_external,'seed-client','memdot.memory.read');
        INSERT INTO operator_bootstrap(id,account_id,issuer,subject,singleton_key)
          VALUES (:operator_bootstrap,:account_id,'https://seed.example','operator',1);
        INSERT INTO source(id,account_id,space_id,title) VALUES (:source,:account_id,:space_id,'seed');
        INSERT INTO source_revision(id,account_id,space_id,source_id,snapshot_sha256,captured_at)
          VALUES (:source_revision,:account_id,:space_id,:source,repeat('a',64),now());
        INSERT INTO source_blob(id,account_id,space_id,source_revision_id,blob_kind,object_key,sha256,byte_count)
          VALUES (:source_blob,:account_id,:space_id,:source_revision,'original','seed/object',repeat('b',64),1);
        INSERT INTO authored_document(id,account_id,space_id,title)
          VALUES (:authored_document,:account_id,:space_id,'seed document');
        INSERT INTO document_revision(id,account_id,space_id,document_id,content_sha256,schema_version)
          VALUES (:document_revision,:account_id,:space_id,:authored_document,repeat('c',64),1);
        INSERT INTO parse_run(id,account_id,space_id,source_revision_id,parser_profile,status)
          VALUES (:parse_run,:account_id,:space_id,:source_revision,'seed','succeeded');
        INSERT INTO document_element(id,account_id,space_id,parse_run_id,element_kind)
          VALUES (:document_element,:account_id,:space_id,:parse_run,'paragraph');
        INSERT INTO provenance_record(id,account_id,space_id,entity_type,entity_id,activity,agent_actor_id,source_revision_id)
          VALUES (:provenance_record,:account_id,:space_id,'source_revision',:source_revision,'created',:actor_id,:source_revision);
        INSERT INTO truth_classification(id,account_id,space_id,entity_type,entity_id,truth_class)
          VALUES (:truth_classification,:account_id,:space_id,'source_revision',:source_revision,'source_assertion');
        INSERT INTO conflict_set(id,account_id,space_id,resolution)
          VALUES (:conflict_set,:account_id,:space_id,'unresolved');
        INSERT INTO conflict_member(id,account_id,conflict_set_id,entity_type,entity_id)
          VALUES (:conflict_member,:account_id,:conflict_set,'source_revision',:source_revision);
        INSERT INTO proposal(id,account_id,space_id,target_type,target_id,truth_class,status)
          VALUES (:proposal,:account_id,:space_id,'document',:authored_document,'derived_proposal','pending');
        INSERT INTO conversation(id,account_id,space_id,source_client,completeness)
          VALUES (:conversation,:account_id,:space_id,'native','complete');
        INSERT INTO conversation_turn(id,account_id,space_id,conversation_id,role,turn_index)
          VALUES (:conversation_turn,:account_id,:space_id,:conversation,'user',0);
        INSERT INTO audit_event(id,account_id,actor_id,event_type,payload)
          VALUES (:audit_event,:account_id,:actor_id,'seed.created','{}');
        INSERT INTO idempotency_record(id,account_id,idempotency_key,fingerprint_sha256,response_status)
          VALUES (:idempotency_record,:account_id,'seed-key',repeat('d',64),200);
        INSERT INTO durable_job(id,account_id,job_type,status)
          VALUES (:durable_job,:account_id,'seed','pending');
        INSERT INTO job_attempt(id,account_id,job_id,attempt_number,status)
          VALUES (:job_attempt,:account_id,:durable_job,1,'pending');
        INSERT INTO projection_state(id,account_id,projection_name)
          VALUES (:projection_state,:account_id,'seed');
        SELECT set_config('app.pointer_outbox_ok','1',true);
        INSERT INTO current_source_revision(id,account_id,space_id,source_id,revision_id)
          VALUES (:current_source_revision,:account_id,:space_id,:source,:source_revision);
        INSERT INTO current_document_revision(id,account_id,space_id,document_id,revision_id)
          VALUES (:current_document_revision,:account_id,:space_id,:authored_document,:document_revision);
        SELECT set_config('app.pointer_outbox_ok','',true);
        INSERT INTO outbox_event(id,account_id,event_type,payload_sha256,payload)
          VALUES (:outbox_event,:account_id,'seed.source',repeat('e',64),'{}');
    """
    for statement in statements.split(";"):
        if statement.strip():
            session.execute(text(statement), params)

    return {
        "account": bundle.account_id,
        "user": bundle.user_id,
        "account_member": member_id,
        "actor": bundle.actor_id,
        "space": space_id,
        **{
            key: value
            for key, value in ids.items()
            if key not in {"actor_external", "document_outbox_event"}
        },
    }
