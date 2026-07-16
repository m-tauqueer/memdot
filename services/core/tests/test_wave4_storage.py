"""Wave 4 object storage adapter tests."""

from __future__ import annotations

import hashlib
import uuid

import pytest
from memdot_core.storage.s3 import MemoryObjectStorage
from memdot_domain.object_keys import assert_key_account_binding
from memdot_domain.ports.object_storage import ObjectKeyParts, ObjectLifecycleClass


def test_memory_storage_immutability_and_verification() -> None:
    storage = MemoryObjectStorage()
    account_id = uuid.uuid4()
    space_id = uuid.uuid4()
    artifact_id = uuid.uuid4()
    data = b"hello world"
    sha = hashlib.sha256(data).hexdigest()
    parts = ObjectKeyParts(
        account_id=account_id,
        space_id=space_id,
        lifecycle=ObjectLifecycleClass.QUARANTINE,
        artifact_id=artifact_id,
        filename="sample.txt",
    )
    key = storage.build_key(parts)
    storage.put_bytes(
        object_key=key,
        data=data,
        content_type="text/plain",
        account_id=account_id,
        sha256=sha,
    )
    meta = storage.verify_upload_completion(
        object_key=key,
        account_id=account_id,
        expected_sha256=sha,
        expected_byte_count=len(data),
    )
    assert meta.byte_count == len(data)
    with pytest.raises(ValueError, match="upload_verification_failed"):
        storage.verify_upload_completion(
            object_key=key,
            account_id=account_id,
            expected_sha256=sha,
            expected_byte_count=len(data) + 1,
        )


def test_cross_account_and_traversal_denied() -> None:
    account_id = uuid.uuid4()
    key = f"accounts/{account_id}/spaces/{uuid.uuid4()}/original/{uuid.uuid4()}/../evil.txt"
    with pytest.raises(ValueError, match="traversal"):
        assert_key_account_binding(key, account_id)
    with pytest.raises(ValueError, match="mismatch"):
        assert_key_account_binding(
            f"accounts/{uuid.uuid4()}/spaces/{uuid.uuid4()}/original/x/y.txt",
            account_id,
        )
