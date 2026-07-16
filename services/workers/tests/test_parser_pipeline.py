"""Parser pipeline golden tests."""

from __future__ import annotations

import uuid

from memdot_domain.ids import parse_run_id
from memdot_provider_adapters.native_text_parser import NativeTextParser
from memdot_workers.ingestion.normalize import validate_parse_result


def test_native_text_deterministic_elements() -> None:
    parser = NativeTextParser()
    revision_id = uuid.uuid4()
    run_id = parse_run_id(revision_id, parser.profile_hash())
    content = b"Line one\nLine two\n"
    first = parser.parse(content=content, mime_type="text/plain", parse_run_id=run_id)
    second = parser.parse(content=content, mime_type="text/plain", parse_run_id=run_id)
    assert [element.element_id for element in first.elements] == [
        element.element_id for element in second.elements
    ]
    assert validate_parse_result(first) == ()


def test_empty_text_quality_gate() -> None:
    parser = NativeTextParser()
    revision_id = uuid.uuid4()
    run_id = parse_run_id(revision_id, parser.profile_hash())
    result = parser.parse(content=b"   \n", mime_type="text/plain", parse_run_id=run_id)
    assert "quality_below_threshold" in validate_parse_result(result)
