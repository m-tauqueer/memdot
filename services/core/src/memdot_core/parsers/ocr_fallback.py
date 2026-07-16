"""Gated OCR fallback seam (stub profile for self-host without GPU OCR)."""

from __future__ import annotations

import hashlib
import json
import uuid

from memdot_domain.ids import element_id
from memdot_domain.ingestion import ElementKind
from memdot_domain.ports.parser import (
    ElementLocator,
    NormalizedElement,
    ParseResult,
    ParserProfile,
)

OCR_QUALITY_THRESHOLD = 0.45


class OcrFallbackParser:
    name = "ocr_paddle_stub"
    profile = ParserProfile.OCR_PADDLE

    def profile_hash(self) -> str:
        return hashlib.sha256(b"ocr_paddle_stub_v1").hexdigest()

    def parse(
        self,
        *,
        content: bytes,
        mime_type: str,
        language_hints: tuple[str, ...] = (),
        parse_run_id: uuid.UUID,
    ) -> ParseResult:
        del content, mime_type
        hint = language_hints[0] if language_hints else "en"
        placeholder = f"[ocr-unavailable:{hint}]"
        content_hash = hashlib.sha256(placeholder.encode("utf-8")).hexdigest()
        canonical_locator = "ocr:page:1"
        element = NormalizedElement(
            element_id=element_id(parse_run_id, canonical_locator, content_hash),
            kind=ElementKind.PARAGRAPH,
            order_index=0,
            parent_element_id=None,
            exact_text=placeholder,
            normalized_text=placeholder,
            content_hash=content_hash,
            locator=ElementLocator(kind="page", value="1"),
            language=hint,
            confidence=0.2,
            warnings=("ocr_stub_only",),
        )
        artifact = json.dumps({"ocr": "stub"}, sort_keys=True).encode("utf-8")
        return ParseResult(
            profile=self.profile,
            profile_hash=self.profile_hash(),
            elements=(element,),
            page_count=1,
            quality_score=0.2,
            raw_artifact_bytes=artifact,
            diagnostics=("ocr_fallback_stub",),
        )
