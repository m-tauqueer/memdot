"""Ingestion limits, element kinds, and processing status domain types."""

from __future__ import annotations

from enum import StrEnum


class SourceProcessingStatus(StrEnum):
    DRAFT = "draft"
    UPLOAD_PENDING = "upload_pending"
    UPLOADED = "uploaded"
    QUEUED = "queued"
    RUNNING = "running"
    PARTIAL = "partial"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ParseRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class ElementKind(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    FORMULA = "formula"
    FIGURE = "figure"
    ASSET = "asset"
    PAGE = "page"
    CODE_BLOCK = "code_block"


class BlobKind(StrEnum):
    ORIGINAL = "original"
    CONNECTOR_SNAPSHOT = "connector_snapshot"
    PARSER_ARTIFACT = "parser_artifact"
    RENDERED_PAGE = "rendered_page"
    ASSET = "asset"
    EXPORT = "export"
    QUARANTINE = "quarantine"


class IngestionLimits:
    """Deployment-configurable safeguards (TRD-ING-002)."""

    max_object_bytes: int = 100 * 1024 * 1024
    max_pages: int = 1000
    max_active_parse_workflows: int = 2
    max_account_queue_depth: int = 100
    max_archive_depth: int = 8
    max_decompressed_bytes: int = 200 * 1024 * 1024
    parse_timeout_seconds: int = 3600
