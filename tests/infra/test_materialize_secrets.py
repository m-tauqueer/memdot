"""Prove templates can materialize required runtime secret files."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_materialize_creates_required_runtime_files() -> None:
    env = os.environ.copy()
    env["FORCE_REMATERIALIZE"] = "1"
    env["MEMDOT_HTTP_PORT"] = "18080"
    env["MEMDOT_HTTPS_PORT"] = "18443"
    result = subprocess.run(
        ["bash", "infra/compose/scripts/materialize_local_secrets.sh"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    secrets = ROOT / "infra" / "compose" / "secrets"
    required = [
        "postgres.env",
        "hatchet.env",
        "keycloak.env",
        "seaweedfs.env",
        "core.env",
        "mcp.env",
        "web.env",
        "workers.env",
        "model-router.env",
        "realm-memdot.runtime.json",
        "s3.runtime.json",
    ]
    for name in required:
        path = secrets / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        assert "REPLACE_WITH_OPERATOR_SECRET" not in text
        assert "memdot-local-dev-only-secret" not in text
        assert "phase2-core-client-secret-not-for-production" not in text
    tls = ROOT / "infra" / "compose" / "tls"
    assert (tls / "ca.crt").is_file()
    assert (tls / "server.crt").is_file()
    assert (tls / "server.key").is_file()
