"""Place service layer."""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.note import Note
from app.models.place import Place
from app.models.tag import Tag
from app.schemas.place import PlaceCreate, PlaceUpdate
from app.utils.text_normalize import normalize_place_name


def _encode_cursor(created_at: datetime, place_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{place_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
    created_at_str, place_id_str = decoded.split("|", 1)
    created_at = datetime.fromisoformat(created_at_str)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return created_at, uuid.UUID(place_id_str)


async def _upsert_tags(db: AsyncSession, tag_names: list[str]) -> list[Tag]:
    cleaned = list({name.strip() for name in tag_names if name.strip()})
    if not cleaned:
        return []

    existing_rows = await db.execute(select(Tag).where(Tag.name.in_(cleaned)))
    existing = {tag.name: tag for tag in existing_rows.scalars().all()}

    to_create = [Tag(name=name) for name in cleaned if name not in existing]
    db.add_all(to_create)
    if to_create:
        await db.flush()

    return [*existing.values(), *to_create]


async def _load_place(db: AsyncSession, place_id: uuid.UUID) -> Place | None:
    stmt = (
        select(Place)
        .options(
            selectinload(Place.provider_links),
            selectinload(Place.tags),
            selectinload(Place.sources),
            selectinload(Place.notes),
            selectinload(Place.visits),
        )
        .where(Place.id == place_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_place(db: AsyncSession, data: PlaceCreate) -> Place:
    """Create a place and attach tags/notes."""
    tag_models = await _upsert_tags(db, data.tags) if data.tags else []

    place = Place(
        canonical_name=data.canonical_name,
        normalized_name=normalize_place_name(data.canonical_name),
        address_road=data.address_road,
        address_jibun=data.address_jibun,
        region_depth1=data.region_depth1,
        region_depth2=data.region_depth2,
        region_depth3=data.region_depth3,
        phone=data.phone,
        category_primary=data.category_primary,
        category_secondary=data.category_secondary,
        parking=data.parking,
        reservation=data.reservation,
        price_range=data.price_range,
        mood=data.mood,
        companions=data.companions,
        situations=data.situations,
        is_favorite=data.is_favorite,
        user_rating=data.user_rating,
    )
    if data.lat is not None and data.lng is not None:
        place.location = WKTElement(f"POINT({data.lng} {data.lat})", srid=4326)

    if tag_models:
        place.tags = tag_models

    db.add(place)
    await db.flush()

    for note_text in data.notes:
        note = note_text.strip()
        if note:
            db.add(Note(place_id=place.id, content=note))

    await db.commit()
    loaded = await _load_place(db, place.id)
    if loaded is None:
        raise RuntimeError("Place was created but could not be loaded")
    return loaded


async def get_place(db: AsyncSession, place_id: uuid.UUID) -> Place | None:
    """Fetch place with child entities."""
    return await _load_place(db, place_id)


async def list_places(
    db: AsyncSession,
    cursor: str | None,
    limit: int,
    category_primary: str | None = None,
    is_favorite: bool | None = None,
) -> tuple[list[Place], str | None, int]:
    """List places with cursor-based pagination."""
    stmt = select(Place).options(selectinload(Place.tags))

    if category_primary:
        stmt = stmt.where(Place.category_primary == category_primary)
    if is_favorite is not None:
        stmt = stmt.where(Place.is_favorite.is_(is_favorite))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = int((await db.execute(total_stmt)).scalar_one())

    if cursor:
        cursor_created_at, cursor_id = _decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                Place.created_at < cursor_created_at,
                and_(Place.created_at == cursor_created_at, Place.id < cursor_id),
            )
        )

    stmt = stmt.order_by(Place.created_at.desc(), Place.id.desc()).limit(limit + 1)
    rows = (await db.execute(stmt)).scalars().all()

    next_cursor: str | None = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last.created_at, last.id)
        rows = rows[:limit]

    return rows, next_cursor, total


async def update_place(db: AsyncSession, place_id: uuid.UUID, data: PlaceUpdate) -> Place | None:
    """Update place fields and replace tags if provided."""
    place = await _load_place(db, place_id)
    if place is None:
        return None

    payload: dict[str, Any] = data.model_dump(exclude_unset=True)

    lat = payload.pop("lat", None)
    lng = payload.pop("lng", None)
    tags = payload.pop("tags", None)

    for key, value in payload.items():
        setattr(place, key, value)

    if data.canonical_name is not None:
        place.normalized_name = normalize_place_name(data.canonical_name)

    if lat is not None and lng is not None:
        place.location = WKTElement(f"POINT({lng} {lat})", srid=4326)

    if tags is not None:
        place.tags = await _upsert_tags(db, tags)

    await db.commit()
    return await _load_place(db, place_id)


async def delete_place(db: AsyncSession, place_id: uuid.UUID) -> bool:
    """Delete place by id."""
    place = await db.get(Place, place_id)
    if place is None:
        return False
    await db.delete(place)
    await db.commit()
    return True
