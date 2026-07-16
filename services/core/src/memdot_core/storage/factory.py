"""Object storage factory for Core runtime."""

from __future__ import annotations

from memdot_core.settings import CoreSettings
from memdot_core.storage.s3 import MemoryObjectStorage, S3ObjectStorage
from memdot_domain.ports.object_storage import ObjectStoragePort


def storage_from_settings(settings: CoreSettings) -> ObjectStoragePort:
    if settings.env == "test" or not settings.object_store_endpoint.strip():
        return MemoryObjectStorage()
    return S3ObjectStorage(
        endpoint_url=settings.object_store_endpoint,
        access_key=settings.object_store_access_key,
        secret_key=settings.object_store_secret_key,
    )
