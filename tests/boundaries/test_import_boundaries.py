"""Dependency-boundary positive checks."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.boundary
def test_import_linter_passes() -> None:
    result = subprocess.run(
        ["lint-imports"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.boundary
def test_workers_cannot_depend_on_ui_package() -> None:
    """Workers must not declare a dependency on the TypeScript UI package."""
    workers_toml = (ROOT / "services" / "workers" / "pyproject.toml").read_text(encoding="utf-8")
    assert "memdot-ui" not in workers_toml
    assert "packages/ui" not in workers_toml


@pytest.mark.boundary
def test_domain_package_has_no_adapters_namespace() -> None:
    providers = ROOT / "packages" / "domain-python" / "src" / "memdot_domain" / "providers"
    assert not providers.exists()
    adapters = (
        ROOT
        / "packages"
        / "provider-adapters"
        / "src"
        / "memdot_provider_adapters"
        / "stub_memory.py"
    )
    assert adapters.is_file()
