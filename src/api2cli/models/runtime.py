from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RequestTiming(BaseModel):
    """Timing information for an HTTP request."""

    start_time: datetime
    end_time: datetime
    duration_ms: float


class RateLimitInfo(BaseModel):
    """Rate limit information from response headers."""

    limit: int | None = None
    remaining: int | None = None
    reset_at: datetime | None = None
    retry_after: int | None = None


class PaginationInfo(BaseModel):
    """Pagination state information."""

    page: int | None = None
    total_pages: int | None = None
    next_cursor: str | None = None
    has_more: bool = False
    total_items: int | None = None
    next_url: str | None = None


class OutputError(BaseModel):
    """Error information in output."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    http_status: int | None = None


class OutputMeta(BaseModel):
    """Metadata about the command execution."""

    command: str | None = None
    url: str | None = None
    method: str | None = None
    timing: RequestTiming | None = None
    rate_limit: RateLimitInfo | None = None
    pagination: PaginationInfo | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class OutputEnvelope(BaseModel):
    """Standard output envelope for all command responses."""

    data: Any = None
    meta: OutputMeta = Field(default_factory=OutputMeta)
    error: OutputError | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class ApiRequest(BaseModel):
    """An HTTP request to be executed."""

    method: str
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    body: Any = None
    timeout: float = 30.0
    extensions: dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel):
    """An HTTP response received from an API."""

    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any = None
    timing: RequestTiming | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)
