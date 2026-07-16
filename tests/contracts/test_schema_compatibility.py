"""Contract serialization and compatibility fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, validate

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "packages" / "contracts" / "schemas"
sys.path.insert(0, str(ROOT))


@pytest.fixture
def problem_schema() -> dict:
    return json.loads((SCHEMAS / "json" / "problem.v1.json").read_text(encoding="utf-8"))


@pytest.mark.contract
def test_problem_json_fixture_validates(problem_schema: dict) -> None:
    payload = {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "code": "internal_error",
    }
    validate(instance=payload, schema=problem_schema)


@pytest.mark.contract
def test_memdot_document_v1_fixture() -> None:
    schema = json.loads(
        (SCHEMAS / "json" / "memdot-document.v1.json").read_text(encoding="utf-8")
    )
    doc_id = "0194f123-4567-7890-abcd-ef1234567890"
    block_id = "0194f123-4567-7890-abcd-ef1234567891"
    payload = {
        "schema": "memdot-document",
        "schemaVersion": 1,
        "documentId": doc_id,
        "root": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "attrs": {"blockId": block_id},
                    "content": [{"type": "text", "text": "Hello."}],
                }
            ],
        },
    }
    validate(instance=payload, schema=schema)
    assert schema["$id"].endswith("document/v1.json")


@pytest.mark.contract
def test_event_additive_field_allowed() -> None:
    schema = json.loads((SCHEMAS / "events" / "scaffold.event.v1.json").read_text(encoding="utf-8"))
    payload = {
        "eventName": "scaffold.phase1.verified.v1",
        "eventVersion": 1,
        "occurredAt": "2026-07-15T00:00:00Z",
        "extraAdditiveField": "ignored-by-consumers",
    }
    validate(instance=payload, schema=schema)


@pytest.mark.contract
def test_event_unknown_major_rejected() -> None:
    schema = json.loads((SCHEMAS / "events" / "scaffold.event.v1.json").read_text(encoding="utf-8"))
    payload = {
        "eventName": "scaffold.phase1.verified.v1",
        "eventVersion": 99,
        "occurredAt": "2026-07-15T00:00:00Z",
    }
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert errors, "Unknown major/eventVersion must be rejected"


@pytest.mark.contract
def test_openapi_generation_is_deterministic() -> None:
    from scripts.generate_openapi import OUT, main

    assert main() == 0
    first = OUT.read_text(encoding="utf-8")
    assert main() == 0
    second = OUT.read_text(encoding="utf-8")
    assert first == second
    assert '"title": "Memdot Core API"' in first
