"""Common API schemas."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class CursorPagination(BaseModel):
    """Cursor pagination request parameters."""

    cursor: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class PaginatedResponse[T](BaseModel):
    """Generic paginated response container."""

    items: list[T]
    next_cursor: str | None = None
    total: int | None = None


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str
