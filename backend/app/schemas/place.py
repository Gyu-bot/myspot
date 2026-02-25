"""Place schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.note import NoteResponse
from app.schemas.source import SourceResponse
from app.schemas.tag import TagResponse
from app.schemas.visit import VisitResponse


class ProviderLinkResponse(BaseModel):
    """Provider link response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    provider_place_id: str | None
    provider_url: str | None


class PlaceCreate(BaseModel):
    """Place create request."""

    canonical_name: str
    address_road: str | None = None
    address_jibun: str | None = None
    region_depth1: str | None = None
    region_depth2: str | None = None
    region_depth3: str | None = None
    lat: float | None = None
    lng: float | None = None
    phone: str | None = None
    category_primary: str | None = None
    category_secondary: str | None = None
    parking: bool | None = None
    reservation: str | None = None
    price_range: str | None = None
    mood: list[str] | None = None
    companions: list[str] | None = None
    situations: list[str] | None = None
    is_favorite: bool = False
    user_rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PlaceUpdate(BaseModel):
    """Place update request."""

    canonical_name: str | None = None
    address_road: str | None = None
    address_jibun: str | None = None
    region_depth1: str | None = None
    region_depth2: str | None = None
    region_depth3: str | None = None
    lat: float | None = None
    lng: float | None = None
    phone: str | None = None
    category_primary: str | None = None
    category_secondary: str | None = None
    parking: bool | None = None
    reservation: str | None = None
    price_range: str | None = None
    mood: list[str] | None = None
    companions: list[str] | None = None
    situations: list[str] | None = None
    is_favorite: bool | None = None
    user_rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] | None = None


class PlaceBrief(BaseModel):
    """Lightweight place schema for list/search."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    canonical_name: str
    category_primary: str | None
    is_favorite: bool
    user_rating: int | None
    created_at: datetime


class PlaceResponse(BaseModel):
    """Place response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    canonical_name: str
    normalized_name: str
    address_road: str | None
    address_jibun: str | None
    region_depth1: str | None
    region_depth2: str | None
    region_depth3: str | None
    phone: str | None
    category_primary: str | None
    category_secondary: str | None
    parking: bool | None
    reservation: str | None
    price_range: str | None
    mood: list[str] | None
    companions: list[str] | None
    situations: list[str] | None
    is_favorite: bool
    user_rating: int | None
    created_at: datetime
    updated_at: datetime
    provider_links: list[ProviderLinkResponse] = Field(default_factory=list)
    tags: list[TagResponse] = Field(default_factory=list)


class PlaceDetail(PlaceResponse):
    """Place detail schema including child entities."""

    sources: list[SourceResponse] = Field(default_factory=list)
    notes: list[NoteResponse] = Field(default_factory=list)
    visits: list[VisitResponse] = Field(default_factory=list)


class DuplicateCandidate(BaseModel):
    """Duplicate candidate returned by dedup service."""

    place_id: uuid.UUID
    canonical_name: str
    score: float
    reasons: list[str]


class PlaceCreateResponse(BaseModel):
    """Create place response including duplicate candidates."""

    place: PlaceResponse
    duplicate_candidates: list[DuplicateCandidate] = Field(default_factory=list)


class MergeRequest(BaseModel):
    """Place merge request payload."""

    merge_with: uuid.UUID


class DuplicateCheckRequest(BaseModel):
    """Payload for duplicate check endpoint."""

    canonical_name: str
    address_road: str | None = None
    lat: float | None = None
    lng: float | None = None
    phone: str | None = None
