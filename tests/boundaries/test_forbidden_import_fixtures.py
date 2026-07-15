"""Deliberately failing fixtures proving meaningful import-linter contracts."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _lint_imports() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["lint-imports"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.boundary
def test_import_linter_baseline_passes() -> None:
    result = _lint_imports()
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.boundary
def test_domain_importing_provider_adapters_is_rejected() -> None:
    violating = (
        ROOT
        / "packages"
        / "domain-python"
        / "src"
        / "memdot_domain"
        / "ports"
        / "_phase1_boundary_probe.py"
    )
    try:
        violating.write_text(
            "from memdot_provider_adapters.stub_memory import StubMemoryProviderAdapter\n"
            "assert StubMemoryProviderAdapter is not None\n",
            encoding="utf-8",
        )
        failed = _lint_imports()
        assert failed.returncode != 0, "Expected import-linter to fail on domain->adapters"
        assert "Domain must not import services or adapters" in (failed.stdout + failed.stderr)
    finally:
        if violating.exists():
            violating.unlink()


@pytest.mark.boundary
def test_core_importing_workers_is_rejected() -> None:
    violating = ROOT / "services" / "core" / "src" / "memdot_core" / "_phase1_boundary_probe.py"
    try:
        violating.write_text(
            "from memdot_workers.settings import WorkersSettings\n"
            "assert WorkersSettings is not None\n",
            encoding="utf-8",
        )
        failed = _lint_imports()
        assert failed.returncode != 0, "Expected import-linter to fail on core->workers"
        assert "Services must not import sibling services" in (failed.stdout + failed.stderr)
    finally:
        if violating.exists():
            violating.unlink()
