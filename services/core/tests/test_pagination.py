"""Pagination cursor signing tests."""

from __future__ import annotations

import time
import uuid

import pytest
from memdot_core.pagination import CursorPayload, decode_cursor, encode_cursor, query_hash


@pytest.fixture(autouse=True)
def _cursor_signing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "CORE_TENANT_CONTEXT_SIGNING_KEY", "test-tenant-context-signing-key-32-bytes"
    )


def test_cursor_round_trip() -> None:
    account_id = uuid.uuid4()
    query = {"limit": 25}
    now = int(time.time())
    payload = CursorPayload(
        account_id=account_id,
        query_hash=query_hash(query),
        sort_value="2026-01-01T00:00:00Z",
        item_id=uuid.uuid4(),
        issued_at=now,
        expires_at=now + 3600,
    )
    token = encode_cursor(payload)
    decoded = decode_cursor(token, account_id=account_id, query=query)
    assert decoded is not None
    assert decoded.item_id == payload.item_id


def test_cursor_tamper_rejected() -> None:
    account_id = uuid.uuid4()
    other = uuid.uuid4()
    query = {"limit": 10}
    now = int(time.time())
    payload = CursorPayload(
        account_id=account_id,
        query_hash=query_hash(query),
        sort_value="x",
        item_id=uuid.uuid4(),
        issued_at=now,
        expires_at=now + 3600,
    )
    token = encode_cursor(payload)
    assert decode_cursor(token, account_id=other, query=query) is None
