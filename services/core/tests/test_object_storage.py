"""Object storage adapter fault tests."""

from __future__ import annotations

import hashlib
import uuid

import pytest
from memdot_core.storage.s3 import MemoryObjectStorage
from memdot_domain.ports.object_storage import ObjectKeyParts, ObjectLifecycleClass


def test_immutable_key_binding() -> None:
    storage = MemoryObjectStorage()
    account = uuid.uuid4()
    other = uuid.uuid4()
    parts = ObjectKeyParts(
        account_id=account,
        space_id=uuid.uuid4(),
        lifecycle=ObjectLifecycleClass.ORIGINAL,
        artifact_id=uuid.uuid4(),
        filename="sample.txt",
    )
    key = storage.build_key(parts)
    data = b"hello"
    sha = hashlib.sha256(data).hexdigest()
    storage.put_bytes(
        object_key=key,
        data=data,
        content_type="text/plain",
        account_id=account,
        sha256=sha,
    )
    meta = storage.verify_upload_completion(
        object_key=key,
        account_id=account,
        expected_sha256=sha,
        expected_byte_count=len(data),
    )
    assert meta.byte_count == 5
    with pytest.raises(ValueError):
        storage.head_object(object_key=key, account_id=other)


def test_checksum_mismatch() -> None:
    storage = MemoryObjectStorage()
    account = uuid.uuid4()
    parts = ObjectKeyParts(
        account_id=account,
        space_id=uuid.uuid4(),
        lifecycle=ObjectLifecycleClass.QUARANTINE,
        artifact_id=uuid.uuid4(),
        filename="bad.txt",
    )
    key = storage.build_key(parts)
    storage.put_bytes(
        object_key=key,
        data=b"x",
        content_type="text/plain",
        account_id=account,
        sha256=hashlib.sha256(b"x").hexdigest(),
    )
    with pytest.raises(ValueError):
        storage.verify_upload_completion(
            object_key=key,
            account_id=account,
            expected_sha256="0" * 64,
            expected_byte_count=1,
        )
