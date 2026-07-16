"""Isolated operational PostgreSQL helpers for Hatchet canary effects.

Uses memdot_ops only — never product/canonical tables.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import psycopg


def ops_database_url() -> str:
    url = os.environ.get("MEMDOT_OPS_DATABASE_URL", "").strip()
    if not url:
        msg = "MEMDOT_OPS_DATABASE_URL is required for canary durable effects"
        raise RuntimeError(msg)
    return url


@contextmanager
def ops_connection() -> Generator[psycopg.Connection[Any], None, None]:
    with psycopg.connect(ops_database_url(), connect_timeout=5) as conn:
        yield conn


def ensure_canary_schema(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ops_canary_effect (
              idempotency_key text PRIMARY KEY,
              effect_token text NOT NULL,
              workflow_run_id text,
              created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ops_canary_barrier (
              barrier_id text PRIMARY KEY,
              released boolean NOT NULL DEFAULT false,
              started boolean NOT NULL DEFAULT false,
              created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
    conn.commit()


def commit_idempotent_effect(
    conn: psycopg.Connection[Any],
    *,
    idempotency_key: str,
    effect_token: str,
    workflow_run_id: str | None,
) -> bool:
    """Insert one durable effect. Returns True if this call inserted the row."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ops_canary_effect (idempotency_key, effect_token, workflow_run_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING idempotency_key
            """,
            (idempotency_key, effect_token, workflow_run_id),
        )
        inserted = cur.fetchone() is not None
    conn.commit()
    return inserted


def count_effects(conn: psycopg.Connection[Any], idempotency_key: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM ops_canary_effect WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    return int(row[0]) if row else 0


def delete_effects(conn: psycopg.Connection[Any], idempotency_key: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ops_canary_effect WHERE idempotency_key = %s",
            (idempotency_key,),
        )
    conn.commit()


def upsert_barrier(conn: psycopg.Connection[Any], barrier_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ops_canary_barrier (barrier_id, released, started)
            VALUES (%s, false, false)
            ON CONFLICT (barrier_id) DO UPDATE
              SET released = false, started = false
            """,
            (barrier_id,),
        )
    conn.commit()


def mark_barrier_started(conn: psycopg.Connection[Any], barrier_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE ops_canary_barrier SET started = true WHERE barrier_id = %s",
            (barrier_id,),
        )
    conn.commit()


def release_barrier(conn: psycopg.Connection[Any], barrier_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE ops_canary_barrier SET released = true WHERE barrier_id = %s",
            (barrier_id,),
        )
    conn.commit()


def barrier_state(conn: psycopg.Connection[Any], barrier_id: str) -> tuple[bool, bool]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT started, released FROM ops_canary_barrier WHERE barrier_id = %s",
            (barrier_id,),
        )
        row = cur.fetchone()
    if not row:
        return False, False
    return bool(row[0]), bool(row[1])


def delete_barrier(conn: psycopg.Connection[Any], barrier_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ops_canary_barrier WHERE barrier_id = %s",
            (barrier_id,),
        )
    conn.commit()


def wait_until_released(
    conn: psycopg.Connection[Any],
    barrier_id: str,
    *,
    poll_sec: float = 0.5,
    max_wait_sec: float = 180.0,
) -> None:
    import time

    deadline = time.monotonic() + max_wait_sec
    while time.monotonic() < deadline:
        _started, released = barrier_state(conn, barrier_id)
        if released:
            return
        time.sleep(poll_sec)
    msg = f"barrier wait timed out barrier_id={barrier_id}"
    raise TimeoutError(msg)
