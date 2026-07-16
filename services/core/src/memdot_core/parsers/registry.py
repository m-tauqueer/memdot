"""Parser selection by sniffed MIME type."""

from __future__ import annotations

from memdot_domain.ports.parser import ParserPort

from memdot_core.parsers.docling_stub import DoclingParserStub
from memdot_core.parsers.native_pdf import NativePdfParser
from memdot_core.parsers.native_text import NativeTextParser
from memdot_core.parsers.ocr_fallback import OcrFallbackParser

_TEXT_MIMES = frozenset({"text/plain", "text/markdown", "text/x-markdown"})
_OFFICE_MIMES = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/msword",
        "application/vnd.ms-powerpoint",
    }
)


def select_parser(mime_type: str, *, ocr_fallback: bool = False) -> ParserPort:
    lowered = mime_type.split(";")[0].strip().lower()
    if ocr_fallback:
        return OcrFallbackParser()
    if lowered in _TEXT_MIMES:
        return NativeTextParser()
    if lowered == "application/pdf":
        return NativePdfParser()
    if lowered in _OFFICE_MIMES:
        return DoclingParserStub()
    return NativeTextParser()
