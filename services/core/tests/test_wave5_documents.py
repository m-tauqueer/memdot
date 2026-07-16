"""Light document API and service tests."""

from __future__ import annotations

import uuid

import pytest
from memdot_domain.document import validate_document_payload
from memdot_domain.ids import new_uuid7

from memdot_core.documents import service as document_service


def test_validate_or_raise_accepts_minimal_doc() -> None:
    doc_id = new_uuid7()
    payload = {
        "schema": "memdot-document",
        "schemaVersion": 1,
        "documentId": str(doc_id),
        "root": {"type": "doc", "content": []},
    }
    document_service.validate_or_raise(payload)
    assert validate_document_payload(payload).documentId == doc_id


def test_stale_base_revision_error_carries_current_id() -> None:
    current = uuid.uuid4()
    exc = document_service.StaleBaseRevisionError(current_revision_id=current)
    assert exc.current_revision_id == current
