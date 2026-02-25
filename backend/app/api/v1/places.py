"""Places API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.place import (
    DuplicateCandidate,
    DuplicateCheckRequest,
    MergeRequest,
    PlaceBrief,
    PlaceCreate,
    PlaceCreateResponse,
    PlaceDetail,
    PlaceResponse,
    PlaceUpdate,
)
from app.services import dedup_service, place_service

router = APIRouter(prefix="/places", tags=["places"])


@router.post("", response_model=PlaceCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_place(payload: PlaceCreate, db: AsyncSession = Depends(get_db)) -> PlaceCreateResponse:
    """Create a place and return duplicate candidates."""
    duplicate_candidates = await dedup_service.check_duplicates(
        db,
        canonical_name=payload.canonical_name,
        lat=payload.lat,
        lng=payload.lng,
        phone=payload.phone,
    )
    place = await place_service.create_place(db, payload)
    return PlaceCreateResponse(
        place=PlaceResponse.model_validate(place),
        duplicate_candidates=[DuplicateCandidate.model_validate(c) for c in duplicate_candidates],
    )


@router.get("", response_model=PaginatedResponse[PlaceBrief])
async def list_places(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    category_primary: str | None = Query(default=None),
    is_favorite: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PlaceBrief]:
    """List places with cursor pagination."""
    items, next_cursor, total = await place_service.list_places(
        db,
        cursor=cursor,
        limit=limit,
        category_primary=category_primary,
        is_favorite=is_favorite,
    )
    return PaginatedResponse[PlaceBrief](
        items=[PlaceBrief.model_validate(item) for item in items],
        next_cursor=next_cursor,
        total=total,
    )


@router.post("/check-duplicates", response_model=list[DuplicateCandidate])
async def check_duplicates(
    payload: DuplicateCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> list[DuplicateCandidate]:
    """Check duplicate candidates without creating a place."""
    return await dedup_service.check_duplicates(
        db,
        canonical_name=payload.canonical_name,
        lat=payload.lat,
        lng=payload.lng,
        phone=payload.phone,
    )


@router.get("/{place_id}", response_model=PlaceDetail)
async def get_place(place_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> PlaceDetail:
    """Get place detail."""
    place = await place_service.get_place(db, place_id)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return PlaceDetail.model_validate(place)


@router.patch("/{place_id}", response_model=PlaceResponse)
async def update_place(place_id: uuid.UUID, payload: PlaceUpdate, db: AsyncSession = Depends(get_db)) -> PlaceResponse:
    """Update place."""
    updated = await place_service.update_place(db, place_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return PlaceResponse.model_validate(updated)


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(place_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response:
    """Delete place."""
    deleted = await place_service.delete_place(db, place_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Place not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{place_id}/merge", response_model=PlaceDetail)
async def merge_place(place_id: uuid.UUID, payload: MergeRequest, db: AsyncSession = Depends(get_db)) -> PlaceDetail:
    """Merge two places into place_id."""
    try:
        merged = await dedup_service.merge_places(db, keep_id=place_id, merge_id=payload.merge_with)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if merged is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return PlaceDetail.model_validate(merged)
