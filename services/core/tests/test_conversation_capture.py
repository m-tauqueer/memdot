"""Conversation turn payload round-trip and no learner events."""

from __future__ import annotations

import pytest
from factories import create_account_bundle
from memdot_core.conversations import service as conversation_service
from memdot_core.request_context import RequestContext
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text

pytestmark = pytest.mark.usefixtures("truncate_tables")


def _ctx(bundle) -> RequestContext:
    return RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=new_uuid7(),
    )


def test_turn_content_round_trip(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = _ctx(bundle)
    created = conversation_service.create_conversation(
        db_session, ctx, space_id=space_id, source_client="native"
    )
    conversation_id = created["conversationId"]
    first = conversation_service.append_turn(
        db_session,
        ctx,
        conversation_id=__import__("uuid").UUID(conversation_id),
        role="user",
        content="hello world",
        client_turn_id="t1",
    )
    assert first is not None
    assert first["content"] == "hello world"
    again = conversation_service.append_turn(
        db_session,
        ctx,
        conversation_id=__import__("uuid").UUID(conversation_id),
        role="user",
        content="hello world",
        client_turn_id="t1",
    )
    assert again is not None
    assert again["idempotent"] is True
    assert again["turnId"] == first["turnId"]

    loaded = conversation_service.get_conversation(
        db_session, ctx, conversation_id=__import__("uuid").UUID(conversation_id)
    )
    assert loaded is not None
    assert loaded["turns"][0]["content"] == "hello world"

    from memdot_core.db.models.ledger import ConversationTurn
    from sqlalchemy import select

    turn = db_session.execute(
        select(ConversationTurn).where(
            ConversationTurn.account_id == bundle.account_id,
            ConversationTurn.client_turn_id == "t1",
        )
    ).scalar_one()
    assert turn.payload_ciphertext is not None
    assert turn.payload_nonce is not None
    assert (turn.payload_json or {}).get("content") is None


def test_conversations_do_not_create_learner_events(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = _ctx(bundle)
    created = conversation_service.create_conversation(
        db_session, ctx, space_id=space_id, source_client="native"
    )
    conversation_service.append_turn(
        db_session,
        ctx,
        conversation_id=__import__("uuid").UUID(created["conversationId"]),
        role="user",
        content="not evidence",
        client_turn_id="t2",
    )
    count = db_session.execute(
        text("SELECT count(*) FROM learner_event WHERE account_id = :aid"),
        {"aid": bundle.account_id},
    ).scalar_one()
    assert count == 0
