"""Parser-neutral extraction port."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from memdot_domain.ingestion import ElementKind


class ParserProfile(StrEnum):
    NATIVE_TEXT = "native_text_v1"
    NATIVE_PDF = "native_pdf_v1"
    NATIVE_OFFICE = "native_office_v1"
    DOCLING = "docling_v1"
    OCR_PADDLE = "ocr_paddle_v1"


@dataclass(frozen=True)
class ElementLocator:
    kind: str
    value: str


@dataclass(frozen=True)
class NormalizedElement:
    element_id: uuid.UUID
    kind: ElementKind
    order_index: int
    parent_element_id: uuid.UUID | None
    exact_text: str
    normalized_text: str
    content_hash: str
    locator: ElementLocator
    language: str | None = None
    confidence: float | None = None
    warnings: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=lambda: dict[str, str]())


@dataclass(frozen=True)
class ParseResult:
    profile: ParserProfile
    profile_hash: str
    elements: tuple[NormalizedElement, ...]
    page_count: int
    quality_score: float
    raw_artifact_bytes: bytes
    diagnostics: tuple[str, ...] = ()


class ParserPort(Protocol):
    name: str
    profile: ParserProfile

    def profile_hash(self) -> str: ...

    def parse(
        self,
        *,
        content: bytes,
        mime_type: str,
        language_hints: tuple[str, ...] = (),
        parse_run_id: uuid.UUID,
    ) -> ParseResult: ...
