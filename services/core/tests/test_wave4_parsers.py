"""Wave 4 parser golden corpus fixtures."""

from __future__ import annotations

import hashlib
import uuid

from memdot_core.parsers.native_pdf import NativePdfParser
from memdot_core.parsers.native_text import NativeTextParser
from memdot_core.parsers.ocr_fallback import OcrFallbackParser
from memdot_domain.ids import parse_run_id


def test_native_text_hindi_and_hinglish_lines() -> None:
    parser = NativeTextParser()
    run_id = parse_run_id(uuid.uuid4(), parser.profile_hash())
    hindi = "यह एक परीक्षण पंक्ति है।\nYe ek Hinglish line hai.\n".encode()
    result = parser.parse(
        content=hindi,
        mime_type="text/plain",
        language_hints=("hi", "en"),
        parse_run_id=run_id,
    )
    assert len(result.elements) == 2
    assert result.quality_score == 1.0


def test_native_pdf_header_and_empty_extraction() -> None:
    parser = NativePdfParser()
    run_id = parse_run_id(uuid.uuid4(), parser.profile_hash())
    minimal = b"%PDF-1.4\n%%EOF"
    result = parser.parse(content=minimal, mime_type="application/pdf", parse_run_id=run_id)
    assert result.quality_score <= 0.2


def test_ocr_stub_is_gated_low_quality() -> None:
    parser = OcrFallbackParser()
    run_id = parse_run_id(uuid.uuid4(), parser.profile_hash())
    result = parser.parse(
        content=b"%PDF-1.4",
        mime_type="application/pdf",
        language_hints=("hi",),
        parse_run_id=run_id,
    )
    assert result.quality_score < 0.45
    assert result.elements[0].warnings


def test_deterministic_element_ids() -> None:
    parser = NativeTextParser()
    revision_id = uuid.uuid4()
    run_id = parse_run_id(revision_id, parser.profile_hash())
    content = b"stable line\n"
    first = parser.parse(content=content, mime_type="text/plain", parse_run_id=run_id)
    second = parser.parse(content=content, mime_type="text/plain", parse_run_id=run_id)
    assert first.elements[0].element_id == second.elements[0].element_id
    assert first.elements[0].content_hash == hashlib.sha256(b"stable line").hexdigest()
