"""Tags API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagResponse

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate, db: AsyncSession = Depends(get_db)) -> TagResponse:
    """Create tag."""
    tag = Tag(name=payload.name.strip(), type=payload.type)
    db.add(tag)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Tag already exists") from exc

    await db.refresh(tag)
    return TagResponse.model_validate(tag)


@router.get("", response_model=list[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)) -> list[TagResponse]:
    """List all tags."""
    rows = (await db.execute(select(Tag).order_by(Tag.name.asc()))).scalars().all()
    return [TagResponse.model_validate(row) for row in rows]
