"""Provider-neutral immutable object storage port."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class ObjectLifecycleClass(StrEnum):
    ORIGINAL = "original"
    ARTIFACT = "artifact"
    QUARANTINE = "quarantine"
    EXPORT = "export"


@dataclass(frozen=True)
class PresignedUpload:
    url: str
    object_key: str
    expires_at: datetime
    headers: dict[str, str]


@dataclass(frozen=True)
class PresignedDownload:
    url: str
    expires_at: datetime


@dataclass(frozen=True)
class StoredObjectMeta:
    object_key: str
    byte_count: int
    sha256: str
    content_type: str | None


@dataclass(frozen=True)
class ObjectKeyParts:
    account_id: uuid.UUID
    space_id: uuid.UUID
    lifecycle: ObjectLifecycleClass
    artifact_id: uuid.UUID
    filename: str


class ObjectStoragePort(Protocol):
    """Immutable object storage; overwrites and cross-account access are forbidden."""

    def build_key(self, parts: ObjectKeyParts) -> str: ...

    def create_presigned_upload(
        self,
        *,
        parts: ObjectKeyParts,
        byte_count: int,
        content_type: str,
        sha256: str,
        expires_seconds: int = 900,
    ) -> PresignedUpload: ...

    def create_presigned_download(
        self,
        *,
        object_key: str,
        account_id: uuid.UUID,
        expires_seconds: int = 900,
    ) -> PresignedDownload: ...

    def head_object(self, *, object_key: str, account_id: uuid.UUID) -> StoredObjectMeta: ...

    def verify_upload_completion(
        self,
        *,
        object_key: str,
        account_id: uuid.UUID,
        expected_sha256: str,
        expected_byte_count: int,
    ) -> StoredObjectMeta: ...

    def promote_from_quarantine(
        self,
        *,
        quarantine_key: str,
        target_parts: ObjectKeyParts,
        account_id: uuid.UUID,
    ) -> StoredObjectMeta: ...

    def read_object_bytes(self, *, object_key: str, account_id: uuid.UUID) -> bytes: ...
