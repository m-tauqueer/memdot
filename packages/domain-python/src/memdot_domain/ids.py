"""UUIDv7 and deterministic UUIDv5 helpers."""

from __future__ import annotations

import os
import time
import uuid


def new_uuid7() -> uuid.UUID:
    """Generate a sortable UUIDv7 (RFC 9562)."""
    unix_ts_ms = int(time.time() * 1000)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF
    value = (unix_ts_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    return uuid.UUID(int=value)


def deterministic_uuid5(namespace: uuid.UUID, name: str) -> uuid.UUID:
    """Deterministic artifact ID where TRD requires UUIDv5."""
    return uuid.uuid5(namespace, name)


SOURCE_REVISION_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
PARSE_RUN_NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
ELEMENT_NAMESPACE = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")


def source_revision_id(source_id: uuid.UUID, snapshot_sha256: str) -> uuid.UUID:
    return deterministic_uuid5(source_id, snapshot_sha256)


def parse_run_id(revision_id: uuid.UUID, profile_hash: str) -> uuid.UUID:
    return deterministic_uuid5(revision_id, profile_hash)


def element_id(
    parse_run_id_value: uuid.UUID, canonical_locator: str, content_hash: str
) -> uuid.UUID:
    return deterministic_uuid5(parse_run_id_value, f"{canonical_locator}:{content_hash}")
