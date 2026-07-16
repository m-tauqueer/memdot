"""Replaceable Docling adapter — fail-closed; native PDF via pypdf when available."""

from __future__ import annotations

import hashlib
import uuid
from io import BytesIO

from memdot_domain.ids import element_id
from memdot_domain.ingestion import ElementKind
from memdot_domain.ports.parser import (
    ElementLocator,
    NormalizedElement,
    ParseResult,
    ParserProfile,
)


def _extract_pdf_texts(content: bytes) -> tuple[list[str], int]:
    """Return (page texts, page_count). Raises ValueError with stable codes."""
    try:
        import importlib

        pypdf = importlib.import_module("pypdf")
        reader = pypdf.PdfReader(BytesIO(content))
    except ImportError as exc:
        msg = "docling_not_configured:pypdf_unavailable"
        raise ValueError(msg) from exc
    except Exception as exc:
        msg = f"docling_not_configured:pdf_extract_failed:{type(exc).__name__}"
        raise ValueError(msg) from exc
    pages = list(getattr(reader, "pages", []) or [])
    page_count = len(pages)
    texts: list[str] = []
    for page in pages:
        extract = getattr(page, "extract_text", None)
        raw = extract() if callable(extract) else ""
        text = str(raw or "").strip()
        if text:
            texts.append(text)
    return texts, page_count


class DoclingParserStub:
    name = "docling_stub"
    profile = ParserProfile.DOCLING

    def profile_hash(self) -> str:
        return "docling_stub_incomplete_v1"

    def parse(
        self,
        *,
        content: bytes,
        mime_type: str,
        language_hints: tuple[str, ...] = (),
        parse_run_id: uuid.UUID,
    ) -> ParseResult:
        del language_hints
        if mime_type != "application/pdf":
            msg = "docling_not_configured"
            raise ValueError(msg)

        texts, page_count = _extract_pdf_texts(content)
        if not texts:
            return ParseResult(
                profile=self.profile,
                profile_hash=self.profile_hash(),
                elements=(),
                page_count=page_count,
                quality_score=0.0,
                raw_artifact_bytes=b'{"docling":"incomplete","code":"pdf_empty_text"}',
                diagnostics=("docling_incomplete", "pdf_empty_text"),
            )
        joined = "\n\n".join(texts)
        content_hash = hashlib.sha256(joined.encode("utf-8")).hexdigest()
        locator = "docling-native:page:1"
        element = NormalizedElement(
            element_id=element_id(parse_run_id, locator, content_hash),
            kind=ElementKind.PARAGRAPH,
            order_index=0,
            parent_element_id=None,
            exact_text=joined,
            normalized_text=joined,
            content_hash=content_hash,
            locator=ElementLocator(kind="page", value="1"),
            warnings=("docling_incomplete_native_pdf_fallback",),
        )
        return ParseResult(
            profile=self.profile,
            profile_hash=self.profile_hash(),
            elements=(element,),
            page_count=page_count,
            quality_score=0.55,
            raw_artifact_bytes=b'{"docling":"incomplete","fallback":"pypdf"}',
            diagnostics=("docling_incomplete", "native_pdf_pypdf_fallback"),
        )
