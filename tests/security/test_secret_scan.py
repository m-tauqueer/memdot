"""Secret scan positive/negative fixture tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_secret_scan() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ROOT / "scripts/secret_scan.sh")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_secret_scan_passes_on_repository() -> None:
    result = run_secret_scan()
    assert result.returncode == 0, result.stdout + result.stderr


def test_secret_scan_ignores_scoped_negative_fixture() -> None:
    text = (ROOT / "tests/security/secret_scan_fixtures/negative_sentinel.txt").read_text()
    assert "SECRET_SCAN_NEGATIVE_FIXTURE" in text
    result = run_secret_scan()
    assert "negative_sentinel.txt" not in (result.stdout + result.stderr)


def test_secret_scan_fails_on_committed_credential() -> None:
    scratch = ROOT / "tests/security/probe_scratch"
    scratch.mkdir(exist_ok=True)
    target = scratch / "_probe.env"
    try:
        target.write_text("AKIA0DUMMYFAKECREDENTIAL01\n", encoding="utf-8")
        result = run_secret_scan()
        assert result.returncode != 0
        assert "_probe.env" in (result.stdout + result.stderr)
    finally:
        target.unlink(missing_ok=True)
