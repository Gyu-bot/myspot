"""Source schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceCreate(BaseModel):
    """Source create request."""

    place_id: uuid.UUID
    type: str = "URL"
    url: str | None = None
    title: str | None = None
    snippet: str | None = None
    raw_text: str | None = None


class SourceResponse(BaseModel):
    """Source response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    place_id: uuid.UUID
    type: str
    url: str | None
    title: str | None
    snippet: str | None
    raw_text: str | None
    captured_at: datetime | None
    created_at: datetime
    updated_at: datetime
