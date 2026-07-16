#!/usr/bin/env python3
"""Backend fast gates with self-provisioned PostgreSQL (Testcontainers).

Provisions Postgres once, migrates empty→head, runs focused Phase 4–8
security/lifecycle tests, then format/lint/type/contracts/build/docs/secret scan.
Fails fast with named steps and guaranteed container cleanup.
"""

from __future__ import annotations

import os
import subprocess
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEP_TIMEOUTS = {
    "migrate": 180,
    "check-rls": 300,
    "pytest": 600,
    "benchmark": 120,
    "format-check": 120,
    "lint": 180,
    "typecheck": 300,
    "contracts": 180,
    "build": 300,
    "docs-validate": 120,
    "secret_scan": 120,
}


def run(step: str, cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    timeout = STEP_TIMEOUTS.get(step, 300)
    print(f"[fast-gates] STEP={step} timeout={timeout}s", flush=True)
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True, env=env, timeout=timeout)


def provision_postgres(env: dict[str, str]) -> tuple[object, str]:
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer("postgres:16-alpine")
    container.start()
    url = container.get_connection_url(driver="psycopg")
    env["MEMDOT_MIGRATION_DATABASE_URL"] = url
    env["MEMDOT_TEST_DATABASE_URL"] = url
    env["TEST_DATABASE_URL"] = url
    env["CORE_DATABASE_URL"] = url
    env["MEMDOT_CHECK_RLS_DATABASE_URL"] = url
    return container, url


def migrate_head(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    os.environ["MEMDOT_MIGRATION_DATABASE_URL"] = url
    root = ROOT / "services" / "core"
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        command.upgrade(cfg, "head")
    print("migration_job=ok", flush=True)


def main() -> int:
    env = os.environ.copy()
    env.setdefault("CORE_SESSION_SIGNING_PEPPER", "test-session-signing-pepper-32bytes")
    env.setdefault("CORE_TENANT_CONTEXT_SIGNING_KEY", "test-tenant-context-signing-key-32-bytes")
    env.setdefault("CORE_JOB_AUTH_SNAPSHOT_KEY", "test-job-auth-snapshot-key-32bytes!!")
    env.setdefault("CORE_CONVERSATION_PAYLOAD_KEY", "test-conversation-payload-key-32b!")
    env.setdefault("CORE_MCP_SERVICE_SECRET", "test-mcp-service-secret-32bytes-xx")
    env.setdefault("CORE_MCP_RESOURCE", "memdot-mcp")
    env.setdefault("CORE_MCP_AUDIENCE_AS_RESOURCE", "true")
    env.setdefault("CORE_OIDC_ISSUER", "https://issuer.example")
    env.setdefault("CORE_OIDC_AUDIENCE", "memdot-mcp")
    env.setdefault("MEMDOT_TENANT_CONTEXT_SIGNING_KEY", env["CORE_TENANT_CONTEXT_SIGNING_KEY"])
    # Fail-fast on first failure; per-suite wall clock is enforced by STEP_TIMEOUTS.
    env["PYTEST_ADDOPTS"] = (env.get("PYTEST_ADDOPTS", "") + " -x").strip()

    container = None
    try:
        print("[fast-gates] STEP=provision-postgres", flush=True)
        container, url = provision_postgres(env)
        print("[fast-gates] STEP=migrate", flush=True)
        migrate_head(url)

        run("check-rls", ["bash", "scripts/check_rls_registry.sh"], env=env)

        phase_tests = [
            "services/core/tests/test_auth_csrf_and_headers_rejected.py",
            "services/core/tests/test_service_auth_mcp.py",
            "services/core/tests/test_signed_job_snapshot.py",
            "services/core/tests/test_processor_auth_snapshot.py",
            "services/core/tests/test_learning_attempt_integrity.py",
            "services/core/tests/test_conversation_capture.py",
            "services/core/tests/test_external_lifecycle.py",
            "services/core/tests/test_resource_limits.py",
            "services/core/tests/test_wave4_parsers.py",
            "packages/domain-python/tests/test_telemetry_allowlist.py",
            "packages/domain-python/tests/test_mcp_domain.py",
            "packages/domain-python/tests/test_learning_domain.py",
            "packages/domain-python/tests/test_memdot_document.py",
            "packages/domain-python/tests/test_retrieval_fusion.py",
            "packages/domain-python/tests/test_context_compiler.py",
        ]
        run("pytest", ["uv", "run", "pytest", *phase_tests, "-q", "--tb=line"], env=env)
        run("benchmark", ["uv", "run", "python", "tests/benchmark/run_benchmarks.py"], env=env)

        run("format-check", ["make", "format-check"], env=env)
        run("lint", ["make", "lint"], env=env)
        run("typecheck", ["make", "typecheck"], env=env)
        run("contracts", ["make", "contracts"], env=env)
        run("build", ["make", "build"], env=env)
        run("docs-validate", ["make", "docs-validate"], env=env)
        run("secret_scan", ["bash", "scripts/secret_scan.sh"], env=env)
        print("backend-fast-gates: PASS", flush=True)
        return 0
    except subprocess.TimeoutExpired as exc:
        print(f"backend-fast-gates: FAIL timeout ({exc})", flush=True)
        return 124
    except subprocess.CalledProcessError as exc:
        print(f"backend-fast-gates: FAIL ({exc})", flush=True)
        return exc.returncode or 1
    except Exception as exc:  # noqa: BLE001 — gate wrapper
        print(f"backend-fast-gates: FAIL ({exc})", flush=True)
        return 1
    finally:
        if container is not None:
            print("[fast-gates] STEP=cleanup-postgres", flush=True)
            try:
                container.stop()
            except Exception as cleanup_exc:  # noqa: BLE001
                print(f"[fast-gates] cleanup warning: {cleanup_exc}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
