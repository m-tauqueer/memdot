"""Ingestion resource limit helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionResourceLimits:
    max_file_bytes: int = 50 * 1024 * 1024
    max_pages: int = 500
    max_archive_entries: int = 200
    max_archive_uncompressed_bytes: int = 200 * 1024 * 1024
    max_recursion_depth: int = 3
    max_decompression_ratio: float = 50.0


DEFAULT_LIMITS = IngestionResourceLimits()


class ResourceLimitExceeded(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def check_file_size(size_bytes: int, *, limits: IngestionResourceLimits = DEFAULT_LIMITS) -> None:
    if size_bytes < 0:
        raise ResourceLimitExceeded("negative_size")
    if size_bytes > limits.max_file_bytes:
        raise ResourceLimitExceeded("file_too_large")


def check_page_count(page_count: int, *, limits: IngestionResourceLimits = DEFAULT_LIMITS) -> None:
    if page_count > limits.max_pages:
        raise ResourceLimitExceeded("too_many_pages")


def check_archive_entry_count(
    entries: int, *, limits: IngestionResourceLimits = DEFAULT_LIMITS
) -> None:
    if entries > limits.max_archive_entries:
        raise ResourceLimitExceeded("too_many_archive_entries")


def check_decompression_ratio(
    compressed: int,
    uncompressed: int,
    *,
    limits: IngestionResourceLimits = DEFAULT_LIMITS,
) -> None:
    if compressed <= 0:
        raise ResourceLimitExceeded("invalid_compressed_size")
    ratio = uncompressed / compressed
    if ratio > limits.max_decompression_ratio:
        raise ResourceLimitExceeded("decompression_ratio_exceeded")
    if uncompressed > limits.max_archive_uncompressed_bytes:
        raise ResourceLimitExceeded("archive_uncompressed_too_large")


def check_recursion_depth(depth: int, *, limits: IngestionResourceLimits = DEFAULT_LIMITS) -> None:
    if depth > limits.max_recursion_depth:
        raise ResourceLimitExceeded("archive_recursion_too_deep")
