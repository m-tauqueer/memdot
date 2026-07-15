#!/usr/bin/env python3
"""Validate versioned JSON Schema and event schema fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
JSON_DIR = ROOT / "packages" / "contracts" / "schemas" / "json"
EVENTS_DIR = ROOT / "packages" / "contracts" / "schemas" / "events"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema_files(directory: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(directory.glob("*.json")):
        try:
            schema = load_json(path)
            Draft202012Validator.check_schema(schema)
        except (json.JSONDecodeError, SchemaError, OSError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    return errors


def main() -> int:
    errors = validate_schema_files(JSON_DIR) + validate_schema_files(EVENTS_DIR)
    if errors:
        print("Schema validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(
        f"Validated {len(list(JSON_DIR.glob('*.json')))} JSON schemas and "
        f"{len(list(EVENTS_DIR.glob('*.json')))} event schemas."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
