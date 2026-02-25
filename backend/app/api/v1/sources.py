"""Sources API endpoints."""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.source import Source
from app.schemas.common import PaginatedResponse
from app.schemas.source import SourceCreate, SourceResponse

router = APIRouter(prefix="/sources", tags=["sources"])


def _encode_cursor(created_at: datetime, source_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{source_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
    created_at_str, source_id_str = decoded.split("|", 1)
    created_at = datetime.fromisoformat(created_at_str)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return created_at, uuid.UUID(source_id_str)


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)) -> SourceResponse:
    """Create source entry."""
    source = Source(**payload.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.get("", response_model=PaginatedResponse[SourceResponse])
async def list_sources(
    place_id: uuid.UUID,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SourceResponse]:
    """List sources for a place with cursor pagination."""
    stmt = select(Source).where(Source.place_id == place_id)
    if cursor:
        cursor_created_at, cursor_id = _decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                Source.created_at < cursor_created_at,
                and_(Source.created_at == cursor_created_at, Source.id < cursor_id),
            )
        )

    stmt = stmt.order_by(Source.created_at.desc(), Source.id.desc()).limit(limit + 1)
    rows = (await db.execute(stmt)).scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last.created_at, last.id)
        rows = rows[:limit]

    return PaginatedResponse[SourceResponse](
        items=[SourceResponse.model_validate(row) for row in rows],
        next_cursor=next_cursor,
        total=None,
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response:
    """Delete source."""
    source = await db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
