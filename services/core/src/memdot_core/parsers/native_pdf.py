"""Minimal PDF text extraction without paid APIs (best-effort native)."""

from __future__ import annotations

import hashlib
import json
import re
import uuid

from memdot_domain.ids import element_id
from memdot_domain.ingestion import ElementKind
from memdot_domain.ports.parser import (
    ElementLocator,
    NormalizedElement,
    ParseResult,
    ParserProfile,
)

_STREAM_TEXT = re.compile(rb"\(([^\\)]*)\)")


class NativePdfParser:
    name = "native_pdf"
    profile = ParserProfile.NATIVE_PDF

    def profile_hash(self) -> str:
        return hashlib.sha256(b"native_pdf_v1").hexdigest()

    def parse(
        self,
        *,
        content: bytes,
        mime_type: str,
        language_hints: tuple[str, ...] = (),
        parse_run_id: uuid.UUID,
    ) -> ParseResult:
        del mime_type, language_hints
        if not content.startswith(b"%PDF"):
            msg = "invalid_pdf_header"
            raise ValueError(msg)
        fragments: list[str] = []
        for match in _STREAM_TEXT.finditer(content[:500_000]):
            piece = match.group(1).decode("latin-1", errors="ignore").strip()
            if piece and len(piece) > 2:
                fragments.append(piece)
        elements: list[NormalizedElement] = []
        for index, fragment in enumerate(fragments[:500]):
            content_hash = hashlib.sha256(fragment.encode("utf-8")).hexdigest()
            canonical_locator = f"pdf-fragment:{index + 1}"
            elements.append(
                NormalizedElement(
                    element_id=element_id(parse_run_id, canonical_locator, content_hash),
                    kind=ElementKind.PARAGRAPH,
                    order_index=index,
                    parent_element_id=None,
                    exact_text=fragment,
                    normalized_text=fragment,
                    content_hash=content_hash,
                    locator=ElementLocator(kind="pdf-fragment", value=str(index + 1)),
                    confidence=0.6 if len(fragment) > 20 else 0.3,
                )
            )
        quality = min(1.0, len(fragments) / 10.0) if fragments else 0.1
        artifact = json.dumps({"fragments": len(fragments)}, sort_keys=True).encode("utf-8")
        return ParseResult(
            profile=self.profile,
            profile_hash=self.profile_hash(),
            elements=tuple(elements),
            page_count=max(1, len(fragments) // 20 + 1),
            quality_score=quality,
            raw_artifact_bytes=artifact,
            diagnostics=("native_pdf_best_effort",),
        )
