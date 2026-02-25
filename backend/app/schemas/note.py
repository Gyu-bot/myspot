"""Note schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    """Note create request."""

    place_id: uuid.UUID
    content: str


class NoteUpdate(BaseModel):
    """Note update request."""

    content: str


class NoteResponse(BaseModel):
    """Note response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    place_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime
