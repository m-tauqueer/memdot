"""Replaceable Docling adapter seam (disabled without explicit configuration)."""

from __future__ import annotations

import uuid

from memdot_domain.ports.parser import ParseResult, ParserProfile


class DoclingParserStub:
    name = "docling_stub"
    profile = ParserProfile.DOCLING

    def profile_hash(self) -> str:
        return "docling_stub_disabled_v1"

    def parse(
        self,
        *,
        content: bytes,
        mime_type: str,
        language_hints: tuple[str, ...] = (),
        parse_run_id: uuid.UUID,
    ) -> ParseResult:
        del content, mime_type, language_hints, parse_run_id
        msg = "docling_not_configured"
        raise ValueError(msg)
