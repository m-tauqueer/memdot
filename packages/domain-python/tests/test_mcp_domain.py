"""MCP domain helpers tests."""

from __future__ import annotations

import uuid

import pytest
from memdot_domain.mcp import (
    CaptureOrigin,
    ConversationCompleteness,
    citation_url,
    decode_mcp_public_id,
    encode_mcp_public_id,
    map_mcp_completeness_to_conversation,
    capture_origin_for_client,
)


def test_mcp_id_round_trip() -> None:
    doc_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    encoded = encode_mcp_public_id("document", doc_id, revision_id=rev_id)
    canonical_type, canonical_id, revision_id = decode_mcp_public_id(encoded)
    assert canonical_type == "document"
    assert canonical_id == doc_id
    assert revision_id == rev_id


def test_invalid_mcp_id_raises() -> None:
    with pytest.raises(ValueError):
        decode_mcp_public_id("bad-id")


def test_completeness_mapping() -> None:
    assert (
        map_mcp_completeness_to_conversation("complete_import")
        == ConversationCompleteness.COMPLETE
    )
    assert (
        map_mcp_completeness_to_conversation("single_turn")
        == ConversationCompleteness.PARTIAL
    )
    assert map_mcp_completeness_to_conversation("bogus") == ConversationCompleteness.UNKNOWN


def test_capture_origin() -> None:
    assert capture_origin_for_client("native") == CaptureOrigin.NATIVE
    assert capture_origin_for_client("chatgpt") == CaptureOrigin.EXTERNAL_MCP


def test_citation_url() -> None:
    doc_id = uuid.uuid4()
    url = citation_url("https://app.example", "document", doc_id)
    assert url == f"https://app.example/library/document/{doc_id}"
