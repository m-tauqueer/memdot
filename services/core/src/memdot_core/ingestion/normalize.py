"""Parser-neutral normalization validation and active parse promotion."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from memdot_domain.ids import new_uuid7
from memdot_domain.ports.parser import ParseResult
from sqlalchemy import text
from sqlalchemy.orm import Session


def validate_parse_result(result: ParseResult) -> list[str]:
    errors: list[str] = []
    if not result.elements and result.quality_score > 0:
        errors.append("empty_elements_with_positive_quality")
    seen_ids: set[uuid.UUID] = set()
    for element in result.elements:
        if element.element_id in seen_ids:
            errors.append("duplicate_element_id")
        seen_ids.add(element.element_id)
        if not element.content_hash or len(element.content_hash) != 64:
            errors.append("invalid_content_hash")
    return errors


def payload_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def promote_active_parse_run(
    db: Session,
    *,
    account_id: uuid.UUID,
    space_id: uuid.UUID,
    source_id: uuid.UUID,
    revision_id: uuid.UUID,
    parse_run_id: uuid.UUID,
    payload: dict[str, Any],
) -> None:
    event_id = new_uuid7()
    pointer_id = new_uuid7()
    digest = payload_sha256(payload)
    db.execute(
        text(
            "SELECT memdot_set_current_active_parse_run("
            ":pointer_id, :account_id, :space_id, :source_id, "
            ":revision_id, :parse_run_id, :event_id, :payload_sha256, CAST(:payload AS jsonb))"
        ),
        {
            "pointer_id": pointer_id,
            "account_id": account_id,
            "space_id": space_id,
            "source_id": source_id,
            "revision_id": revision_id,
            "parse_run_id": parse_run_id,
            "event_id": event_id,
            "payload_sha256": digest,
            "payload": json.dumps(payload),
        },
    )
