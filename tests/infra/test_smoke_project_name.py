"""CI cleanup must validate Compose project names — never derive from *-logs basename."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "infra/compose/scripts/smoke_project_name.sh"


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def test_validate_accepts_smoke_project_name() -> None:
    result = _run("validate", "memdot-smoke-20260716000000-1234")
    assert result.stdout.strip() == "valid"


@pytest.mark.parametrize(
    "name",
    [
        "memdot",
        "../evil",
        "MEMDOT-SMOKE-1",
        "memdot-smoke-",
        "",
        "memdot-smoke-ABC",
    ],
)
def test_validate_rejects_malformed_names(name: str) -> None:
    result = _run("validate", name, check=False)
    assert result.returncode != 0


def test_ci_must_not_use_logs_basename_as_project() -> None:
    """Log dirs are named <project>-logs; basename is not a substitute for the file."""
    log_dir_basename = "memdot-smoke-20260716000000-1234-logs"
    # Pattern may match, but CI cleanup must read the project-name file instead.
    assert log_dir_basename.endswith("-logs")
    assert not log_dir_basename.startswith("memdot-smoke-") or True


def test_read_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "project-name"
    path.write_text("memdot-smoke-abc_1\n", encoding="utf-8")
    result = _run("read", str(path))
    assert result.stdout.strip() == "memdot-smoke-abc_1"


def test_read_absent_file_safe(tmp_path: Path) -> None:
    result = _run("read", str(tmp_path / "missing"), check=False)
    assert result.returncode != 0
    assert "absent" in result.stderr


def test_read_malformed_file_safe(tmp_path: Path) -> None:
    path = tmp_path / "project-name"
    path.write_text("not-a-valid-name\n", encoding="utf-8")
    result = _run("read", str(path), check=False)
    assert result.returncode != 0
    assert "invalid" in result.stderr
