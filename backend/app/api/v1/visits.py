"""Visits API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.visit import Visit
from app.schemas.visit import VisitCreate, VisitResponse

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(payload: VisitCreate, db: AsyncSession = Depends(get_db)) -> VisitResponse:
    """Create visit record."""
    visit = Visit(**payload.model_dump())
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return VisitResponse.model_validate(visit)


@router.get("", response_model=list[VisitResponse])
async def list_visits(place_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[VisitResponse]:
    """List visits by place."""
    stmt = select(Visit).where(Visit.place_id == place_id).order_by(Visit.visited_at.desc(), Visit.id.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [VisitResponse.model_validate(row) for row in rows]
