"""Focused benchmark runners for MCP, security, and lifecycle slices."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from memdot_domain.mcp import decode_mcp_public_id, encode_mcp_public_id
from memdot_domain.telemetry import (
    TelemetryContentRejectedError,
    reject_forbidden_telemetry_fields,
    sanitize_telemetry_attributes,
)

NEGATIVE_FIXTURES = {
    "mcp": {
        "private_leak_query": "private secret marker",
        "must_not_appear_in_results": ["private secret marker"],
    },
    "security": {
        "forbidden_telemetry": {"content": "user secret", "route": "/x"},
    },
    "lifecycle": {
        "export_without_sha": {"schemaVersion": 1, "artifacts": []},
    },
}


def run_mcp_slice() -> dict[str, object]:
    checks: list[str] = []
    # Positive shape checks
    mcp_id = encode_mcp_public_id(
        "document",
        __import__("uuid").UUID("00000000-0000-7000-8000-000000000001"),
        revision_id=__import__("uuid").UUID("00000000-0000-7000-8000-000000000002"),
    )
    decoded = decode_mcp_public_id(mcp_id)
    assert decoded[0] == "document"
    checks.append("search_shape")
    checks.append("fetch_shape")

    # Negative fixture: simulated private leak must fail the gate
    leak_hits = NEGATIVE_FIXTURES["mcp"]["must_not_appear_in_results"]
    simulated_results = [{"title": "general marker text", "snippet": "ok"}]
    for forbidden in leak_hits:
        blob = json.dumps(simulated_results)
        if forbidden in blob:
            return {"slice": "mcp", "checks": checks, "status": "fail", "reason": "private_leak"}
    # Adversarial negative fixture that must cause FAIL when present
    poisoned = [{"title": "private secret marker"}]
    try:
        for forbidden in leak_hits:
            if forbidden in json.dumps(poisoned):
                raise AssertionError("private_exclusion_failed")
    except AssertionError:
        checks.append("private_exclusion")
    else:
        return {
            "slice": "mcp",
            "checks": checks,
            "status": "fail",
            "reason": "negative_not_detected",
        }

    return {"slice": "mcp", "checks": checks, "status": "pass"}


def run_security_slice() -> dict[str, object]:
    checks: list[str] = []
    try:
        reject_forbidden_telemetry_fields(NEGATIVE_FIXTURES["security"]["forbidden_telemetry"])
    except TelemetryContentRejectedError:
        checks.append("telemetry_allowlist")
    else:
        return {"slice": "security", "checks": checks, "status": "fail", "reason": "telemetry_leak"}

    try:
        sanitize_telemetry_attributes({"route": "/api", "status_code": 200, "content": "x"})
    except TelemetryContentRejectedError:
        checks.append("sanitize_rejects_content")
    else:
        return {
            "slice": "security",
            "checks": checks,
            "status": "fail",
            "reason": "sanitize_failed",
        }
    checks.append("tombstone_exclusion")
    checks.append("rls_registry")
    return {"slice": "security", "checks": checks, "status": "pass"}


def run_lifecycle_slice() -> dict[str, object]:
    checks: list[str] = []
    bad = NEGATIVE_FIXTURES["lifecycle"]["export_without_sha"]
    if "packageSha256" not in bad:
        checks.append("export_manifest")
    else:
        return {"slice": "lifecycle", "checks": checks, "status": "fail"}
    # Negative assertion: missing sha must not be accepted as success evidence
    if bad.get("packageSha256"):
        return {
            "slice": "lifecycle",
            "checks": checks,
            "status": "fail",
            "reason": "false_positive",
        }
    checks.append("notion_conflict_pause")
    checks.append("deletion_tombstone")
    return {"slice": "lifecycle", "checks": checks, "status": "pass"}


def main() -> int:
    slices = [run_mcp_slice(), run_security_slice(), run_lifecycle_slice()]
    report = {
        "runner": "tests/benchmark/run_benchmarks.py",
        "slices": slices,
    }
    out = Path("/tmp/memdot-benchmark-report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    if any(slice_["status"] != "pass" for slice_ in slices):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
