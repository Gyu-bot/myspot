"""Tag schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TagCreate(BaseModel):
    """Tag creation request."""

    name: str
    type: str = "freeform"


class TagResponse(BaseModel):
    """Tag response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str
    created_at: datetime
    updated_at: datetime
