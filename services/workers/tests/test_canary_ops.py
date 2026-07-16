"""Focused unit tests for Hatchet canary durable-effect helpers and runner gates."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from memdot_workers.canary_gates import (
    CanaryTimeoutError,
    UnexpectedCanaryFailure,
    is_expected_terminal_failure,
    sync_result_with_timeout,
)
from memdot_workers.canary_ops_db import (
    commit_idempotent_effect,
    count_effects,
    ensure_canary_schema,
    release_barrier,
    upsert_barrier,
)


class _FakeConn:
    def __init__(self) -> None:
        self.rows: dict[str, tuple[str, str | None]] = {}
        self._pending: Any = None

    def cursor(self) -> _FakeConn:
        return self

    def __enter__(self) -> _FakeConn:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        text = " ".join(sql.split()).lower()
        if text.startswith("create table"):
            self._pending = None
            return
        if "insert into ops_canary_effect" in text and params is not None:
            key, token, run_id = params
            if key in self.rows:
                self._pending = None
            else:
                self.rows[key] = (token, run_id)
                self._pending = (key,)
            return
        if "select count(*)" in text and params is not None:
            key = params[0]
            self._pending = (1 if key in self.rows else 0,)
            return
        self._pending = None

    def fetchone(self) -> Any:
        return self._pending

    def commit(self) -> None:
        return None


def test_unique_constraint_yields_one_durable_effect() -> None:
    conn = _FakeConn()
    ensure_canary_schema(conn)  # type: ignore[arg-type]
    first = commit_idempotent_effect(
        conn,  # type: ignore[arg-type]
        idempotency_key="k1",
        effect_token="t1",
        workflow_run_id="r1",
    )
    second = commit_idempotent_effect(
        conn,  # type: ignore[arg-type]
        idempotency_key="k1",
        effect_token="t2",
        workflow_run_id="r2",
    )
    assert first is True
    assert second is False
    assert count_effects(conn, "k1") == 1  # type: ignore[arg-type]


def test_sync_result_timeout_raises_canary_timeout() -> None:
    class _Ref:
        def result(self) -> Any:
            async def _hang() -> dict[str, str]:
                await asyncio.sleep(2)
                return {"ok": "true"}

            return _hang()

    with pytest.raises(CanaryTimeoutError):
        sync_result_with_timeout(_Ref(), timeout_sec=0.2)


def test_expected_terminal_failure_requires_workflow_errors() -> None:
    assert is_expected_terminal_failure(
        Exception("Workflow Errors: ['intentional canary failure']")
    )
    assert not is_expected_terminal_failure(ConnectionError("connection reset"))
    assert not is_expected_terminal_failure(CanaryTimeoutError("timeout"))
    assert not is_expected_terminal_failure(Exception("transport boom"))
    assert not is_expected_terminal_failure(StopAsyncIteration())


def test_unexpected_transport_failure_not_controlled() -> None:
    exc = UnexpectedCanaryFailure("grpc unavailable")
    assert not is_expected_terminal_failure(exc)


def test_count_effects_after_duplicate_submission_path() -> None:
    conn = _FakeConn()
    ensure_canary_schema(conn)  # type: ignore[arg-type]
    for _ in range(3):
        commit_idempotent_effect(
            conn,  # type: ignore[arg-type]
            idempotency_key="dup",
            effect_token="x",
            workflow_run_id=None,
        )
    assert count_effects(conn, "dup") == 1  # type: ignore[arg-type]


@patch("memdot_workers.canary_ops_db.ops_connection")
def test_barrier_helpers_roundtrip(mock_conn: MagicMock) -> None:
    conn = _FakeConn()
    mock_conn.return_value.__enter__.return_value = conn
    upsert_barrier(conn, "b1")  # type: ignore[arg-type]
    release_barrier(conn, "b1")  # type: ignore[arg-type]


def test_sync_result_success_path() -> None:
    class _Ref:
        def result(self) -> Any:
            async def _ok() -> dict[str, str]:
                return {"status": "ok"}

            return _ok()

    assert sync_result_with_timeout(_Ref(), timeout_sec=2.0) == {"status": "ok"}
