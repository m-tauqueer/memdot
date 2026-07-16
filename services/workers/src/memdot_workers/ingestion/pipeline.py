"""Wave 4 ingestion pipeline orchestration (worker-local)."""

from __future__ import annotations

import uuid

from memdot_domain.ids import parse_run_id as deterministic_parse_run_id
from memdot_domain.ingestion import ParseRunStatus
from memdot_provider_adapters.native_text_parser import NativeTextParser
from memdot_workers.ingestion.normalize import referential_integrity, validate_parse_result


def select_parser(mime_type: str) -> NativeTextParser:
    if mime_type.startswith("text/") or mime_type in {"application/json"}:
        return NativeTextParser()
    return NativeTextParser()


def run_ingestion_pipeline(
    *,
    revision_id: uuid.UUID,
    content: bytes,
    mime_type: str,
) -> tuple[uuid.UUID, ParseRunStatus, tuple[str, ...]]:
    parser = select_parser(mime_type)
    profile_hash = parser.profile_hash()
    run_id = deterministic_parse_run_id(revision_id, profile_hash)
    result = parser.parse(content=content, mime_type=mime_type, parse_run_id=run_id)
    errors = validate_parse_result(result)
    if errors or not referential_integrity(result.elements):
        return run_id, ParseRunStatus.FAILED, errors
    return run_id, ParseRunStatus.SUCCEEDED, ()
