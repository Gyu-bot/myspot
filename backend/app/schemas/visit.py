"""Visit schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class VisitCreate(BaseModel):
    """Visit creation request."""

    place_id: uuid.UUID
    visited_at: date
    rating: int | None = None
    with_whom: str | None = None
    situation: str | None = None
    memo: str | None = None
    revisit: bool | None = None


class VisitResponse(BaseModel):
    """Visit response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    place_id: uuid.UUID
    visited_at: date
    rating: int | None
    with_whom: str | None
    situation: str | None
    memo: str | None
    revisit: bool | None
    created_at: datetime
    updated_at: datetime
