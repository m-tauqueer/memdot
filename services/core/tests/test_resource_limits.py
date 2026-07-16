"""Ingestion resource limit helpers."""

from __future__ import annotations

import pytest
from memdot_core.parsers.resource_limits import (
    ResourceLimitExceeded,
    check_archive_entry_count,
    check_decompression_ratio,
    check_file_size,
    check_page_count,
    check_recursion_depth,
)


def test_file_size_limit() -> None:
    check_file_size(10)
    with pytest.raises(ResourceLimitExceeded, match="file_too_large"):
        check_file_size(51 * 1024 * 1024)


def test_page_and_archive_limits() -> None:
    check_page_count(10)
    with pytest.raises(ResourceLimitExceeded, match="too_many_pages"):
        check_page_count(501)
    with pytest.raises(ResourceLimitExceeded, match="too_many_archive_entries"):
        check_archive_entry_count(201)
    with pytest.raises(ResourceLimitExceeded, match="decompression_ratio"):
        check_decompression_ratio(1, 1000)
    with pytest.raises(ResourceLimitExceeded, match="archive_recursion"):
        check_recursion_depth(4)
