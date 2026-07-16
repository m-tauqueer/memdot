"""UUID generation tests."""

from __future__ import annotations

import uuid

from memdot_domain.ids import SOURCE_REVISION_NAMESPACE, deterministic_uuid5, new_uuid7


def test_uuid7_is_version_7() -> None:
    value = new_uuid7()
    assert value.version == 7


def test_uuid7_sortable() -> None:
    values = {new_uuid7() for _ in range(32)}
    assert len(values) == 32


def test_uuid5_deterministic() -> None:
    source_id = new_uuid7()
    first = deterministic_uuid5(source_id, "deadbeef")
    second = deterministic_uuid5(source_id, "deadbeef")
    assert first == second
    assert first.version == 5


def test_source_revision_namespace_is_uuid() -> None:
    assert isinstance(SOURCE_REVISION_NAMESPACE, uuid.UUID)
