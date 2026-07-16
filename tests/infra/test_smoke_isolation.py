"""Smoke isolation: concurrent lock rejection and runtime-dir targeting."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / "infra/compose/scripts/selfhost_smoke.sh"


def test_concurrent_smoke_rejected() -> None:
    """Holding the flock causes a second smoke invocation to refuse immediately."""
    with tempfile.TemporaryDirectory(prefix="memdot-smoke-lock-test-") as tmp:
        lock = Path(tmp) / "lock"
        # Acquire exclusive lock in this process, then invoke smoke briefly.
        with open(lock, "w", encoding="utf-8") as handle:
            # flock via Python fcntl
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            env = {
                **os.environ,
                "MEMDOT_SMOKE_LOCK_FILE": str(lock),
                "MEMDOT_SMOKE_PROJECT": "memdot-smoke-concurrent-test",
                "MEMDOT_SMOKE_RUNTIME_DIR": str(Path(tmp) / "runtime"),
                "MEMDOT_SMOKE_LOG_DIR": str(Path(tmp) / "logs"),
                "MEMDOT_SMOKE_PROJECT_NAME_FILE": str(Path(tmp) / "project-name"),
            }
            result = subprocess.run(
                ["bash", str(SMOKE)],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            assert result.returncode == 1
            combined = result.stdout + result.stderr
            assert "concurrent_smoke" in combined
