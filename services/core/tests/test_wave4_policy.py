"""Wave 4 policy layer tests: pagination, idempotency, problem details."""

from __future__ import annotations

import os
import time
import uuid

import pytest
from factories import create_account_bundle
from memdot_core.errors import ErrorCode, FieldError, problem_response, validation_problem
from memdot_core.idempotency import begin_idempotency, fingerprint_request
from memdot_core.pagination import CursorPayload, decode_cursor, encode_cursor, query_hash
from memdot_core.request_context import correlation_id_for_request
from starlette.requests import Request


@pytest.fixture(autouse=True)
def cursor_signing_key() -> None:
    os.environ["CORE_CURSOR_SIGNING_KEY"] = "test-cursor-signing-key-32-bytes-min"


def test_problem_response_shape() -> None:
    correlation = uuid.uuid4()
    response = problem_response(
        status=422,
        code=ErrorCode.VALIDATION_ERROR,
        detail="Invalid field.",
        correlation_id=correlation,
        errors=[FieldError(pointer="/title", code=ErrorCode.VALIDATION_ERROR)],
    )
    body = response.body.decode()
    assert "application/problem+json" in response.media_type
    assert str(correlation) in body
    assert "validation_error" in body


def test_validation_problem_pointer() -> None:
    response = validation_problem(
        errors=[FieldError(pointer="/cursor", code=ErrorCode.CURSOR_INVALID)],
    )
    assert response.status_code == 422


def test_cursor_binding_and_tamper_rejection() -> None:
    account_id = uuid.uuid4()
    query = {"filter": "sources", "limit": 10}
    now = int(time.time())
    payload = CursorPayload(
        account_id=account_id,
        query_hash=query_hash(query),
        sort_value="2026-01-01",
        item_id=uuid.uuid4(),
        issued_at=now,
        expires_at=now + 3600,
    )
    token = encode_cursor(payload)
    decoded = decode_cursor(token, account_id=account_id, query=query)
    assert decoded is not None
    assert decoded.item_id == payload.item_id
    assert decode_cursor(token, account_id=uuid.uuid4(), query=query) is None
    tampered = token[:-4] + ("aaaa" if token[-4] != "a" else "bbbb")
    assert decode_cursor(tampered, account_id=account_id, query=query) is None


def test_idempotency_replay_and_conflict(db_session, truncate_tables) -> None:
    bundle, _space = create_account_bundle(db_session)
    fingerprint_a = fingerprint_request(method="POST", path="/api/v1/sources", body=b"{}")
    fingerprint_b = fingerprint_request(method="POST", path="/api/v1/sources", body=b'{"x":1}')
    first = begin_idempotency(
        db_session,
        account_id=bundle.account_id,
        route="POST /api/v1/sources",
        idempotency_key="key-1",
        fingerprint=fingerprint_a,
    )
    assert not first.replay and not first.conflict
    replay = begin_idempotency(
        db_session,
        account_id=bundle.account_id,
        route="POST /api/v1/sources",
        idempotency_key="key-1",
        fingerprint=fingerprint_a,
    )
    assert replay.replay and not replay.conflict
    conflict = begin_idempotency(
        db_session,
        account_id=bundle.account_id,
        route="POST /api/v1/sources",
        idempotency_key="key-1",
        fingerprint=fingerprint_b,
    )
    assert conflict.conflict and not conflict.replay


def test_correlation_id_from_header() -> None:
    correlation = uuid.uuid4()
    scope = {
        "type": "http",
        "method": "GET",
        "headers": [(b"x-correlation-id", str(correlation).encode())],
        "query_string": b"",
        "path": "/",
    }
    request = Request(scope)
    assert correlation_id_for_request(request) == correlation
