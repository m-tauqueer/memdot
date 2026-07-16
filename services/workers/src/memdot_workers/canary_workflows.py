"""Content-free Hatchet canary workflows (SDK 0.47 / server 0.55).

Durable effects land in isolated memdot_ops tables under a unique
idempotency_key constraint. Metadata-only keys are never treated as proof.
"""

from __future__ import annotations

import uuid

from hatchet_sdk import Context, Hatchet

from memdot_workers.canary_ops_db import (
    commit_idempotent_effect,
    ensure_canary_schema,
    mark_barrier_started,
    ops_connection,
    wait_until_released,
)

hatchet = Hatchet(debug=False)


@hatchet.workflow(name="memdot-ops-canary")
class MemdotOpsCanary:
    @hatchet.step(timeout="60s", retries=2)
    def ops_effect(self, context: Context) -> dict[str, str]:
        inp = context.workflow_input() or {}
        idempotency_key = str(inp.get("idempotency_key", "")).strip()
        if not idempotency_key:
            msg = "idempotency_key required"
            raise ValueError(msg)
        effect_token = str(inp.get("effect_token") or uuid.uuid4())
        run_id = getattr(context, "workflow_run_id", None) or inp.get("workflow_run_id")
        with ops_connection() as conn:
            ensure_canary_schema(conn)
            inserted = commit_idempotent_effect(
                conn,
                idempotency_key=idempotency_key,
                effect_token=effect_token,
                workflow_run_id=str(run_id) if run_id else None,
            )
        return {
            "status": "ok",
            "purpose": "ops-canary",
            "inserted": "true" if inserted else "false",
        }


@hatchet.workflow(name="memdot-ops-canary-barrier")
class MemdotOpsCanaryBarrier:
    @hatchet.step(timeout="180s", retries=0)
    def ops_barrier_effect(self, context: Context) -> dict[str, str]:
        inp = context.workflow_input() or {}
        idempotency_key = str(inp.get("idempotency_key", "")).strip()
        barrier_id = str(inp.get("barrier_id", "")).strip()
        if not idempotency_key or not barrier_id:
            msg = "idempotency_key and barrier_id required"
            raise ValueError(msg)
        effect_token = str(inp.get("effect_token") or uuid.uuid4())
        run_id = getattr(context, "workflow_run_id", None) or inp.get("workflow_run_id")
        with ops_connection() as conn:
            ensure_canary_schema(conn)
            mark_barrier_started(conn, barrier_id)
        # Hold until operator/shell releases the barrier (engine may restart meanwhile).
        with ops_connection() as conn:
            wait_until_released(conn, barrier_id, max_wait_sec=170.0)
            inserted = commit_idempotent_effect(
                conn,
                idempotency_key=idempotency_key,
                effect_token=effect_token,
                workflow_run_id=str(run_id) if run_id else None,
            )
        return {
            "status": "ok",
            "purpose": "ops-canary-barrier",
            "inserted": "true" if inserted else "false",
        }


@hatchet.workflow(name="memdot-ops-canary-fail")
class MemdotOpsCanaryFail:
    @hatchet.step(timeout="30s", retries=0)
    def ops_fail(self, context: Context) -> dict[str, str]:
        msg = "intentional canary failure"
        raise RuntimeError(msg)
