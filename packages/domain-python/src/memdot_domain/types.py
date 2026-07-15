"""Shared domain value types (scaffold)."""

from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ComponentHealth(BaseModel):
    """Content-free health payload for skeleton endpoints."""

    status: HealthStatus = HealthStatus.OK
    component: str = Field(min_length=1)
