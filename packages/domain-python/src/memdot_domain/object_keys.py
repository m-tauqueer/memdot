"""Deterministic immutable object key construction."""

from __future__ import annotations

import re
import uuid

from memdot_domain.ports.object_storage import ObjectKeyParts, ObjectLifecycleClass

_FILENAME_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    cleaned = _FILENAME_SAFE.sub("_", filename.strip())[:128]
    return cleaned or "object"


def build_object_key(parts: ObjectKeyParts) -> str:
    """Account/space-bound immutable key with traversal prevention."""
    if ".." in parts.filename or parts.filename.startswith("/"):
        msg = "invalid object filename"
        raise ValueError(msg)
    safe_name = sanitize_filename(parts.filename)
    return (
        f"accounts/{parts.account_id}/spaces/{parts.space_id}/"
        f"{parts.lifecycle.value}/{parts.artifact_id}/{safe_name}"
    )


def assert_key_account_binding(object_key: str, account_id: uuid.UUID) -> None:
    expected_prefix = f"accounts/{account_id}/"
    if not object_key.startswith(expected_prefix):
        msg = "object_key_account_mismatch"
        raise ValueError(msg)
    if ".." in object_key:
        msg = "object_key_traversal_denied"
        raise ValueError(msg)


def quarantine_key(account_id: uuid.UUID, upload_id: uuid.UUID, filename: str) -> str:
    return build_object_key(
        ObjectKeyParts(
            account_id=account_id,
            space_id=upload_id,
            lifecycle=ObjectLifecycleClass.QUARANTINE,
            artifact_id=upload_id,
            filename=filename,
        )
    )
