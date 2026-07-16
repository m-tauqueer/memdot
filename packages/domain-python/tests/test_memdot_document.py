"""MemdotDocument validation and extraction tests."""

from __future__ import annotations

import uuid

import pytest
from memdot_domain.document import (
    DocumentValidationError,
    content_sha256,
    document_from_markdown,
    document_to_html,
    document_to_markdown,
    extract_plain_text,
    validate_document_payload,
)
from memdot_domain.ids import new_uuid7


def _sample_doc(*, document_id: uuid.UUID | None = None) -> dict:
    doc_id = document_id or new_uuid7()
    block_id = new_uuid7()
    return {
        "schema": "memdot-document",
        "schemaVersion": 1,
        "documentId": str(doc_id),
        "root": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "attrs": {"blockId": str(block_id)},
                    "content": [{"type": "text", "text": "Hello memory."}],
                }
            ],
        },
    }


def test_validate_document_round_trip() -> None:
    payload = _sample_doc()
    doc = validate_document_payload(payload)
    assert doc.documentId == uuid.UUID(payload["documentId"])
    assert extract_plain_text(doc) == "Hello memory."
    assert content_sha256(doc) == content_sha256(payload)


def test_rejects_non_https_link() -> None:
    payload = _sample_doc()
    payload["root"]["content"][0]["content"] = [
        {
            "type": "text",
            "text": "bad",
            "marks": [{"type": "link", "attrs": {"href": "http://example.com"}}],
        }
    ]
    with pytest.raises(DocumentValidationError):
        validate_document_payload(payload)


def test_markdown_import_export() -> None:
    doc_id = new_uuid7()
    payload = document_from_markdown("# Title\n\nBody", document_id=doc_id)
    validate_document_payload(payload)
    assert "Title" in document_to_markdown(payload)
    assert "<h1>" in document_to_html(payload)
