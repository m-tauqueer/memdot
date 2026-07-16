"""Core-owned S3 object storage (provider-adapters remain worker-local)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from memdot_domain.object_keys import assert_key_account_binding, build_object_key
from memdot_domain.ports.object_storage import (
    ObjectKeyParts,
    ObjectStoragePort,
    PresignedDownload,
    PresignedUpload,
    StoredObjectMeta,
)


class S3ObjectStorage(ObjectStoragePort):
    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str = "memdot",
    ) -> None:
        import boto3
        from botocore.config import Config

        self._bucket = bucket
        self._client = boto3.client(  # type: ignore[reportUnknownMemberType]
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )

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
        assert_key_account_binding(key, parts.account_id)
        url = str(
            self._client.generate_presigned_url(  # type: ignore[reportUnknownMemberType]
                "put_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": key,
                    "ContentType": content_type,
                    "ContentLength": byte_count,
                    "Metadata": {"sha256": sha256, "account_id": str(parts.account_id)},
                },
                ExpiresIn=expires_seconds,
            )
        )
        return PresignedUpload(
            url=url,
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
        url = str(
            self._client.generate_presigned_url(  # type: ignore[reportUnknownMemberType]
                "get_object",
                Params={"Bucket": self._bucket, "Key": object_key},
                ExpiresIn=expires_seconds,
            )
        )
        return PresignedDownload(
            url=url,
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_seconds),
        )

    def head_object(self, *, object_key: str, account_id: uuid.UUID) -> StoredObjectMeta:
        assert_key_account_binding(object_key, account_id)
        resp = cast(
            dict[str, Any],
            self._client.head_object(Bucket=self._bucket, Key=object_key),  # type: ignore[reportUnknownMemberType]
        )
        meta = cast(dict[str, str], resp.get("Metadata", {}))
        sha = meta.get("sha256") or hashlib.sha256(b"").hexdigest()
        content_type = resp.get("ContentType")
        return StoredObjectMeta(
            object_key=object_key,
            byte_count=int(resp["ContentLength"]),
            sha256=sha,
            content_type=str(content_type) if content_type is not None else None,
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
        if meta.byte_count != expected_byte_count:
            msg = "upload_byte_count_mismatch"
            raise ValueError(msg)
        if meta.sha256.lower() != expected_sha256.lower():
            msg = "upload_checksum_mismatch"
            raise ValueError(msg)
        return meta

    def promote_from_quarantine(
        self,
        *,
        quarantine_key: str,
        target_parts: ObjectKeyParts,
        account_id: uuid.UUID,
    ) -> StoredObjectMeta:
        assert_key_account_binding(quarantine_key, account_id)
        target_key = self.build_key(target_parts)
        self._client.copy_object(  # type: ignore[reportUnknownMemberType]
            Bucket=self._bucket,
            CopySource={"Bucket": self._bucket, "Key": quarantine_key},
            Key=target_key,
            MetadataDirective="COPY",
        )
        return self.head_object(object_key=target_key, account_id=account_id)

    def read_object_bytes(self, *, object_key: str, account_id: uuid.UUID) -> bytes:
        assert_key_account_binding(object_key, account_id)
        resp = cast(
            dict[str, Any],
            self._client.get_object(Bucket=self._bucket, Key=object_key),  # type: ignore[reportUnknownMemberType]
        )
        body = resp["Body"]
        data = cast(bytes, body.read())
        return data


class MemoryObjectStorage(ObjectStoragePort):
    """In-process storage for unit tests."""

    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str, dict[str, str]]] = {}

    def build_key(self, parts: ObjectKeyParts) -> str:
        return build_object_key(parts)

    def put_bytes(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str,
        account_id: uuid.UUID,
        sha256: str,
    ) -> None:
        assert_key_account_binding(object_key, account_id)
        self._objects[object_key] = (data, content_type, {"sha256": sha256})

    def read_object_bytes(self, *, object_key: str, account_id: uuid.UUID) -> bytes:
        assert_key_account_binding(object_key, account_id)
        data, _content_type, _meta = self._objects[object_key]
        return data

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
