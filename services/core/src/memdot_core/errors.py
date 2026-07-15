"""Stable error-code registry ownership (scaffold)."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Stable public error codes. Feature-specific codes arrive with features."""

    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    VALIDATION_ERROR = "validation_error"
