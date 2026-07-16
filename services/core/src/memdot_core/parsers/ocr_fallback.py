"""Gated OCR fallback seam — fail-closed stub that never emits promotable content."""

from __future__ import annotations

import hashlib
import json
import uuid

from memdot_domain.ports.parser import ParseResult, ParserProfile

OCR_QUALITY_THRESHOLD = 0.45


class OcrFallbackParser:
    name = "ocr_paddle_stub"
    profile = ParserProfile.OCR_PADDLE

    def profile_hash(self) -> str:
        return hashlib.sha256(b"ocr_paddle_stub_v2_fail_closed").hexdigest()

    def parse(
        self,
        *,
        content: bytes,
        mime_type: str,
        language_hints: tuple[str, ...] = (),
        parse_run_id: uuid.UUID,
    ) -> ParseResult:
        """Never return synthetic user-visible content that can be promoted."""
        del content, mime_type, language_hints, parse_run_id
        artifact = json.dumps(
            {"ocr": "stub", "status": "failed", "code": "ocr_stub_unavailable"},
            sort_keys=True,
        ).encode("utf-8")
        return ParseResult(
            profile=self.profile,
            profile_hash=self.profile_hash(),
            elements=(),
            page_count=0,
            quality_score=0.0,
            raw_artifact_bytes=artifact,
            diagnostics=("ocr_stub_unavailable", "ocr_fail_closed", "not_promotable"),
        )
