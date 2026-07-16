"""Run content-free Hatchet canary workflows against server 0.55 / SDK 0.47.

Proves durable idempotent effects in memdot_ops (unique constraint), bounded
timeouts, expected terminal failure, and accepted-work recovery across an
engine restart barrier coordinated by the shell.

Never prints tokens. Avoids os._exit when the SDK permits graceful shutdown.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from typing import Any

from memdot_workers.canary_gates import (
    CanaryTimeoutError,
    is_expected_terminal_failure,
    sync_result_with_timeout,
)
from memdot_workers.canary_ops_db import (
    barrier_state,
    count_effects,
    delete_barrier,
    delete_effects,
    ensure_canary_schema,
    ops_connection,
    release_barrier,
    upsert_barrier,
)


def _timeout_sec() -> float:
    raw = os.environ.get("MEMDOT_CANARY_TIMEOUT_SEC", "120").strip()
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 120.0


def _shutdown_worker(worker: Any) -> None:
    import asyncio
    import inspect

    for name in ("exit_gracefully", "close"):
        method = getattr(worker, name, None)
        if not callable(method):
            continue
        try:
            result = method()
            if inspect.isawaitable(result):
                asyncio.run(result)
            print(f"worker_shutdown method={name}")
            return
        except Exception as exc:  # noqa: BLE001 — best-effort cleanup
            print(f"worker_shutdown_warn method={name} err={type(exc).__name__}")
    print("worker_shutdown method=none")


def _prepare_client_env() -> None:
    token = os.environ.get("HATCHET_CLIENT_TOKEN", "").strip()
    if not token:
        token_file = os.environ.get("HATCHET_CLIENT_TOKEN_FILE", "").strip()
        if token_file:
            from pathlib import Path

            token = Path(token_file).read_text(encoding="utf-8").strip()
            os.environ["HATCHET_CLIENT_TOKEN"] = token
    if not os.environ.get("HATCHET_CLIENT_TOKEN", "").strip():
        print("hatchet_canary_failed reason=missing_token", file=sys.stderr)
        raise SystemExit(1)

    os.environ.setdefault("HATCHET_CLIENT_TLS_STRATEGY", "none")
    if "HATCHET_CLIENT_HOST_PORT" not in os.environ:
        host = os.environ.get("WORKERS_HATCHET_HOST", "hatchet-engine")
        port = os.environ.get("WORKERS_HATCHET_PORT", "7070")
        os.environ["HATCHET_CLIENT_HOST_PORT"] = f"{host}:{port}"


def run_standard_canary(hatchet: Any, timeout_sec: float) -> int:
    idempotency = os.environ.get("MEMDOT_CANARY_IDEMPOTENCY_KEY", f"canary-{int(time.time())}")
    effect_token = str(uuid.uuid4())
    print("hatchet_canary_submit idempotency_key_present=true")

    with ops_connection() as conn:
        ensure_canary_schema(conn)
        delete_effects(conn, idempotency)

    payload = {"idempotency_key": idempotency, "effect_token": effect_token}
    success_ref = hatchet.admin.run_workflow("memdot-ops-canary", payload)
    run_id = getattr(success_ref, "workflow_run_id", None) or str(success_ref)
    print(f"hatchet_canary_accepted run_id_present={bool(run_id)} run_id={run_id}")

    # Duplicate submission: Hatchet may accept a second delivery; durable effect must stay 1.
    # Do not sync_result the duplicate — concurrent listeners race the SDK event loop.
    duplicate_accepted = False
    try:
        dup_ref = hatchet.admin.run_workflow("memdot-ops-canary", payload)
        duplicate_accepted = True
        print(
            "duplicate_submission_accepted="
            f"{bool(getattr(dup_ref, 'workflow_run_id', None) or dup_ref)}"
        )
    except Exception as exc:  # noqa: BLE001 — engine may reject duplicate
        print(f"duplicate_submission_rejected detail={type(exc).__name__}")

    try:
        sync_result_with_timeout(success_ref, timeout_sec)
    except CanaryTimeoutError:
        print("hatchet_canary_failed reason=timeout path=success", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(
            f"hatchet_canary_failed reason=unexpected_terminal detail={type(exc).__name__}",
            file=sys.stderr,
        )
        return 1
    print("terminal_state=SUCCEEDED")

    with ops_connection() as conn:
        effect_count = count_effects(conn, idempotency)
    print(f"durable_effect_count={effect_count} duplicate_accepted={duplicate_accepted}")
    if effect_count != 1:
        print(
            f"hatchet_canary_failed reason=idempotency_effect_count count={effect_count}",
            file=sys.stderr,
        )
        return 1
    print("idempotent_effect_ok=true")

    # Controlled failure: require Hatchet workflow-error terminal with expected text.
    fail_ref = hatchet.admin.run_workflow(
        "memdot-ops-canary-fail",
        {"marker": "controlled-fail"},
    )
    fail_run_id = getattr(fail_ref, "workflow_run_id", None) or str(fail_ref)
    print(f"controlled_failure_run_id_present={bool(fail_run_id)}")
    try:
        sync_result_with_timeout(fail_ref, timeout_sec)
    except CanaryTimeoutError:
        print("hatchet_canary_failed reason=timeout path=controlled_failure", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        if not is_expected_terminal_failure(exc):
            print(
                f"hatchet_canary_failed reason=unexpected_failure_type detail={type(exc).__name__}",
                file=sys.stderr,
            )
            return 1
        print("controlled_failure_detected=true terminal_state=FAILED")
    else:
        print("hatchet_canary_failed reason=controlled_failure_succeeded", file=sys.stderr)
        return 1

    # Timeout path: hold a barrier without releasing, require sync_result wrapper
    # to raise CanaryTimeoutError (no blocking sleep in a step).
    timeout_key = f"{idempotency}-timeout"
    timeout_barrier = f"barrier-{timeout_key}"
    with ops_connection() as conn:
        delete_effects(conn, timeout_key)
        upsert_barrier(conn, timeout_barrier)
    hang_ref = hatchet.admin.run_workflow(
        "memdot-ops-canary-barrier",
        {
            "idempotency_key": timeout_key,
            "barrier_id": timeout_barrier,
            "effect_token": str(uuid.uuid4()),
        },
    )
    hang_budget = min(15.0, timeout_sec)
    hold_deadline = time.monotonic() + min(30.0, timeout_sec)
    while time.monotonic() < hold_deadline:
        with ops_connection() as conn:
            started, _released = barrier_state(conn, timeout_barrier)
        if started:
            break
        time.sleep(0.25)
    try:
        sync_result_with_timeout(hang_ref, hang_budget)
    except CanaryTimeoutError:
        print("timeout_path_detected=true reason=listener_timeout")
    except Exception as exc:  # noqa: BLE001
        print(
            f"hatchet_canary_failed reason=unexpected_timeout_path detail={type(exc).__name__}",
            file=sys.stderr,
        )
        with ops_connection() as conn:
            release_barrier(conn, timeout_barrier)
        return 1
    else:
        print("hatchet_canary_failed reason=timeout_path_succeeded", file=sys.stderr)
        with ops_connection() as conn:
            release_barrier(conn, timeout_barrier)
        return 1

    # Release so the held step can finish; do not re-enter sync_result on the
    # timed-out listener (a background waiter may still be draining).
    with ops_connection() as conn:
        release_barrier(conn, timeout_barrier)
    time.sleep(2)
    with ops_connection() as conn:
        delete_effects(conn, idempotency)
        delete_effects(conn, timeout_key)
        delete_barrier(conn, timeout_barrier)
    print("hatchet_canary_state=ok")
    return 0


def run_barrier_hold(hatchet: Any, timeout_sec: float) -> int:
    """Submit barrier workflow, wait until started, then await terminal after release."""
    idempotency = os.environ.get(
        "MEMDOT_CANARY_IDEMPOTENCY_KEY", f"canary-barrier-{int(time.time())}"
    )
    barrier_id = os.environ.get("MEMDOT_CANARY_BARRIER_ID", f"barrier-{idempotency}")
    effect_token = str(uuid.uuid4())

    with ops_connection() as conn:
        ensure_canary_schema(conn)
        delete_effects(conn, idempotency)
        upsert_barrier(conn, barrier_id)

    payload = {
        "idempotency_key": idempotency,
        "barrier_id": barrier_id,
        "effect_token": effect_token,
    }
    ref = hatchet.admin.run_workflow("memdot-ops-canary-barrier", payload)
    run_id = getattr(ref, "workflow_run_id", None) or str(ref)
    print(f"accepted_run_id={run_id}")
    print(f"barrier_id={barrier_id}")
    print("barrier_holding=true")
    sys.stdout.flush()

    # Wait until the step marks started (accepted work is outstanding, not terminal).
    started_deadline = time.monotonic() + min(60.0, timeout_sec)
    while time.monotonic() < started_deadline:
        with ops_connection() as conn:
            started, released = barrier_state(conn, barrier_id)
        if started and not released:
            print("barrier_started=true run_not_terminal=true")
            sys.stdout.flush()
            break
        time.sleep(0.5)
    else:
        print("hatchet_canary_failed reason=barrier_never_started", file=sys.stderr)
        return 1

    # Block until shell releases barrier (after engine restart) then await terminal.
    release_deadline = time.monotonic() + timeout_sec
    while time.monotonic() < release_deadline:
        with ops_connection() as conn:
            _started, released = barrier_state(conn, barrier_id)
        if released:
            break
        time.sleep(0.5)
    else:
        print("hatchet_canary_failed reason=timeout path=barrier_release", file=sys.stderr)
        return 2

    try:
        sync_result_with_timeout(ref, timeout_sec)
    except CanaryTimeoutError:
        print("hatchet_canary_failed reason=timeout path=barrier_success", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(
            f"hatchet_canary_failed reason=barrier_terminal detail={type(exc).__name__}",
            file=sys.stderr,
        )
        return 1

    with ops_connection() as conn:
        effect_count = count_effects(conn, idempotency)
        delete_effects(conn, idempotency)
        delete_barrier(conn, barrier_id)
    print(f"barrier_terminal_state=SUCCEEDED same_run_id={run_id}")
    print(f"durable_effect_count={effect_count}")
    if effect_count != 1:
        print(
            f"hatchet_canary_failed reason=barrier_effect_count count={effect_count}",
            file=sys.stderr,
        )
        return 1
    print("accepted_work_restart_ok=true")
    return 0


def run_release_only() -> int:
    """Shell helper: release barrier after hatchet-engine restart."""
    barrier_id = os.environ.get("MEMDOT_CANARY_BARRIER_ID", "").strip()
    if not barrier_id:
        print("hatchet_canary_failed reason=missing_barrier_id", file=sys.stderr)
        return 1
    with ops_connection() as conn:
        ensure_canary_schema(conn)
        release_barrier(conn, barrier_id)
    print(f"barrier_released=true barrier_id={barrier_id}")
    return 0


def main() -> int:
    mode = os.environ.get("MEMDOT_CANARY_MODE", "standard").strip().lower()
    if mode == "release":
        return run_release_only()

    _prepare_client_env()
    timeout_sec = _timeout_sec()
    print(f"canary_timeout_sec={timeout_sec}")

    # Import after token/env are set so module-level Hatchet() binds correctly.
    from memdot_workers.canary_workflows import (
        MemdotOpsCanary,
        MemdotOpsCanaryBarrier,
        MemdotOpsCanaryFail,
        hatchet,
    )

    worker = hatchet.worker("memdot-ops-canary-worker", max_runs=4)
    worker.register_workflow(MemdotOpsCanary())
    worker.register_workflow(MemdotOpsCanaryBarrier())
    worker.register_workflow(MemdotOpsCanaryFail())
    thread = threading.Thread(target=worker.start, name="hatchet-canary-worker", daemon=True)
    thread.start()
    time.sleep(5)

    exit_code = 1
    try:
        if mode == "barrier":
            exit_code = run_barrier_hold(hatchet, timeout_sec)
        else:
            exit_code = run_standard_canary(hatchet, timeout_sec)
    except Exception as exc:  # noqa: BLE001
        print(
            f"hatchet_canary_failed reason=unhandled detail={type(exc).__name__}",
            file=sys.stderr,
        )
        exit_code = 1
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        _shutdown_worker(worker)
        time.sleep(1)
        # Compose one-shot must return; worker threads may keep the process alive
        # even after awaited exit_gracefully. Prefer graceful first, then hard exit.
        os._exit(exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
