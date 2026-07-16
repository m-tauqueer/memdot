"""MCP public ID mapping, capture completeness, and citation helpers."""

from __future__ import annotations

import uuid
from enum import StrEnum


class ConversationCompleteness(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    SUMMARY = "summary"
    UNKNOWN = "unknown"


class McpInteractionCompleteness(StrEnum):
    SINGLE_TURN = "single_turn"
    PARTIAL_THREAD = "partial_thread"
    COMPLETE_IMPORT = "complete_import"


class CaptureOrigin(StrEnum):
    NATIVE = "native"
    EXTERNAL_MCP = "external_mcp"
    IMPORT = "import"


MCP_ID_PREFIX = "memdot"


def encode_mcp_public_id(
    canonical_type: str,
    canonical_id: uuid.UUID,
    *,
    revision_id: uuid.UUID | None = None,
) -> str:
    """Stable opaque MCP id for company-knowledge-compatible search/fetch."""
    parts = [MCP_ID_PREFIX, canonical_type, str(canonical_id)]
    if revision_id is not None:
        parts.append(str(revision_id))
    return ":".join(parts)


def decode_mcp_public_id(mcp_id: str) -> tuple[str, uuid.UUID, uuid.UUID | None]:
    """Decode an MCP public id into canonical type, id, and optional revision."""
    parts = mcp_id.split(":")
    if len(parts) < 3 or parts[0] != MCP_ID_PREFIX:
        msg = "invalid mcp public id"
        raise ValueError(msg)
    canonical_type = parts[1]
    try:
        canonical_id = uuid.UUID(parts[2])
    except ValueError as exc:
        msg = "invalid mcp public id"
        raise ValueError(msg) from exc
    revision_id: uuid.UUID | None = None
    if len(parts) >= 4:
        try:
            revision_id = uuid.UUID(parts[3])
        except ValueError as exc:
            msg = "invalid mcp public id"
            raise ValueError(msg) from exc
    return canonical_type, canonical_id, revision_id


def map_mcp_completeness_to_conversation(value: str) -> ConversationCompleteness:
    """Map MCP record_interaction completeness to stored conversation labels."""
    normalized = value.strip().lower()
    if normalized == McpInteractionCompleteness.COMPLETE_IMPORT:
        return ConversationCompleteness.COMPLETE
    if normalized == McpInteractionCompleteness.PARTIAL_THREAD:
        return ConversationCompleteness.PARTIAL
    if normalized == McpInteractionCompleteness.SINGLE_TURN:
        return ConversationCompleteness.PARTIAL
    if normalized in ConversationCompleteness:
        return ConversationCompleteness(normalized)
    return ConversationCompleteness.UNKNOWN


def capture_origin_for_client(source_client: str) -> CaptureOrigin:
    """Derive capture origin from the conversation source client label."""
    lowered = source_client.strip().lower()
    if lowered in {"native", "memdot", "first_party"}:
        return CaptureOrigin.NATIVE
    if lowered in {"import", "bulk_import"}:
        return CaptureOrigin.IMPORT
    return CaptureOrigin.EXTERNAL_MCP


def citation_url(
    public_base_url: str,
    canonical_type: str,
    canonical_id: uuid.UUID,
) -> str:
    """Absolute user-openable citation URL (reauthorizes in the web app)."""
    base = public_base_url.rstrip("/")
    return f"{base}/library/{canonical_type}/{canonical_id}"
