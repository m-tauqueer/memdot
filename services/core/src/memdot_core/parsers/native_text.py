"""Native text/markdown parser for Core ingestion (no paid APIs)."""

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


class NativeTextParser:
    name = "native_text"
    profile = ParserProfile.NATIVE_TEXT

    def profile_hash(self) -> str:
        return hashlib.sha256(b"native_text_v1").hexdigest()

    def parse(
        self,
        *,
        content: bytes,
        mime_type: str,
        language_hints: tuple[str, ...] = (),
        parse_run_id: uuid.UUID,
    ) -> ParseResult:
        del mime_type
        text = content.decode("utf-8", errors="replace")
        lines = [line for line in text.splitlines() if line.strip()]
        elements: list[NormalizedElement] = []
        for index, line in enumerate(lines):
            content_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
            canonical_locator = f"line:{index + 1}"
            elements.append(
                NormalizedElement(
                    element_id=element_id(parse_run_id, canonical_locator, content_hash),
                    kind=ElementKind.PARAGRAPH,
                    order_index=index,
                    parent_element_id=None,
                    exact_text=line,
                    normalized_text=line.strip(),
                    content_hash=content_hash,
                    locator=ElementLocator(kind="line", value=str(index + 1)),
                    language=language_hints[0] if language_hints else None,
                    confidence=1.0,
                )
            )
        artifact = json.dumps({"lines": len(lines)}, sort_keys=True).encode("utf-8")
        quality = 1.0 if lines else 0.0
        return ParseResult(
            profile=self.profile,
            profile_hash=self.profile_hash(),
            elements=tuple(elements),
            page_count=max(1, len(lines) // 40 + 1),
            quality_score=quality,
            raw_artifact_bytes=artifact,
        )
