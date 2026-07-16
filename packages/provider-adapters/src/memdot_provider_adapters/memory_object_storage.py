"""In-memory object storage adapter for tests and worker fixtures."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from memdot_domain.object_keys import assert_key_account_binding, build_object_key
from memdot_domain.ports.object_storage import (
    ObjectKeyParts,
    ObjectStoragePort,
    PresignedDownload,
    PresignedUpload,
    StoredObjectMeta,
)


class MemoryObjectStorageAdapter(ObjectStoragePort):
    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str, dict[str, str]]] = {}

    def put_bytes(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str,
        account_id: uuid.UUID,
        sha256: str | None = None,
    ) -> None:
        assert_key_account_binding(object_key, account_id)
        digest = sha256 or hashlib.sha256(data).hexdigest()
        self._objects[object_key] = (data, content_type, {"sha256": digest})

    def build_key(self, parts: ObjectKeyParts) -> str:
        return build_object_key(parts)

    def create_presigned_upload(
        self,
        *,
        parts: ObjectKeyParts,
        byte_count: int,
        content_type: str,
        sha256: str,
        expires_seconds: int = 900,
    ) -> PresignedUpload:
        key = self.build_key(parts)
        return PresignedUpload(
            url=f"memory://upload/{key}",
            object_key=key,
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_seconds),
            headers={"Content-Type": content_type},
        )

    def create_presigned_download(
        self,
        *,
        object_key: str,
        account_id: uuid.UUID,
        expires_seconds: int = 900,
    ) -> PresignedDownload:
        assert_key_account_binding(object_key, account_id)
        return PresignedDownload(
            url=f"memory://download/{object_key}",
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_seconds),
        )

    def head_object(self, *, object_key: str, account_id: uuid.UUID) -> StoredObjectMeta:
        assert_key_account_binding(object_key, account_id)
        data, content_type, meta = self._objects[object_key]
        return StoredObjectMeta(
            object_key=object_key,
            byte_count=len(data),
            sha256=meta.get("sha256", hashlib.sha256(data).hexdigest()),
            content_type=content_type,
        )

    def verify_upload_completion(
        self,
        *,
        object_key: str,
        account_id: uuid.UUID,
        expected_sha256: str,
        expected_byte_count: int,
    ) -> StoredObjectMeta:
        meta = self.head_object(object_key=object_key, account_id=account_id)
        if meta.byte_count != expected_byte_count or meta.sha256.lower() != expected_sha256.lower():
            msg = "upload_verification_failed"
            raise ValueError(msg)
        return meta

    def promote_from_quarantine(
        self,
        *,
        quarantine_key: str,
        target_parts: ObjectKeyParts,
        account_id: uuid.UUID,
    ) -> StoredObjectMeta:
        data, content_type, meta = self._objects[quarantine_key]
        target_key = self.build_key(target_parts)
        self._objects[target_key] = (data, content_type, meta)
        return self.head_object(object_key=target_key, account_id=account_id)

    def read_object_bytes(self, *, object_key: str, account_id: uuid.UUID) -> bytes:
        assert_key_account_binding(object_key, account_id)
        data, _content_type, _meta = self._objects[object_key]
        return data
