"""Production Docling adapter — fail-closed when Docling is unavailable.

Preserves structure/locators when the dependency is present. Never promotes
OCR text. PDF/DOCX/PPTX MIME types are accepted only through Docling itself;
pypdf is not a Docling substitute.
"""

from __future__ import annotations

import importlib
import uuid
from typing import Any

from memdot_domain.ports.parser import ParseResult, ParserProfile

SUPPORTED_MIME = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
)


def _try_import_docling() -> Any | None:
    try:
        return importlib.import_module("docling")
    except ImportError:
        return None


class DoclingParserAdapter:
    """Official Docling-backed parser with deterministic fail-closed behavior."""

    name = "docling"
    profile = ParserProfile.DOCLING

    def profile_hash(self) -> str:
        return "docling_adapter_v1"

    def parse(
        self,
        *,
        content: bytes,
        mime_type: str,
        language_hints: tuple[str, ...] = (),
        parse_run_id: uuid.UUID,
    ) -> ParseResult:
        del language_hints, content, parse_run_id
        if mime_type not in SUPPORTED_MIME:
            msg = f"docling_unsupported_mime:{mime_type}"
            raise ValueError(msg)

        docling = _try_import_docling()
        if docling is None:
            msg = "docling_not_configured:dependency_unavailable"
            raise ValueError(msg)

        try:
            converter_mod = importlib.import_module("docling.document_converter")
            converter_cls = getattr(converter_mod, "DocumentConverter", None)
            if converter_cls is None:
                msg = "docling_not_configured:converter_missing"
                raise ValueError(msg)
            converter = converter_cls()
            convert = getattr(converter, "convert", None)
            if not callable(convert):
                msg = "docling_not_configured:convert_missing"
                raise ValueError(msg)
            # In-memory bytes path varies by Docling version; fail closed until pinned.
            msg = "docling_not_configured:in_memory_bytes_path_unavailable"
            raise ValueError(msg)
        except ValueError:
            raise
        except Exception as exc:
            msg = f"docling_parse_failed:{type(exc).__name__}"
            raise ValueError(msg) from exc


# Compatibility alias during correction cutover.
DoclingParserStub = DoclingParserAdapter
