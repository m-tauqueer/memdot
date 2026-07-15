"""TypeScript / Python serialization equivalence for problem+json fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.contract
def test_python_problem_matches_schema_and_shared_fixture() -> None:
    schema = json.loads(
        (ROOT / "packages/contracts/schemas/json/problem.v1.json").read_text(encoding="utf-8")
    )
    from memdot_core.errors import ErrorCode

    payload = {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "code": ErrorCode.INTERNAL_ERROR.value,
    }
    validate(instance=payload, schema=schema)

    fixture = json.loads(
        (ROOT / "tests/contracts/fixtures/problem.v1.example.json").read_text(encoding="utf-8")
    )
    assert fixture == payload
