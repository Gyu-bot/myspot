"""Duplicate detection and merge service."""

from __future__ import annotations

import uuid

from geoalchemy2 import Geography
from sqlalchemy import delete, func, literal, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditLog
from app.models.media import Media
from app.models.note import Note
from app.models.place import Place, ProviderLink
from app.models.source import Source
from app.models.tag import PlaceTag
from app.models.visit import Visit
from app.schemas.place import DuplicateCandidate
from app.utils.text_normalize import normalize_phone, normalize_place_name


async def check_duplicates(
    db: AsyncSession,
    canonical_name: str,
    lat: float | None = None,
    lng: float | None = None,
    phone: str | None = None,
    exclude_place_id: uuid.UUID | None = None,
) -> list[DuplicateCandidate]:
    """Find duplicate candidates using weighted scoring."""
    normalized_name = normalize_place_name(canonical_name)
    normalized_phone = normalize_phone(phone) if phone else None

    name_similarity = func.similarity(Place.normalized_name, normalized_name).label("name_similarity")
    point = None
    within_50m = literal(False)

    if lat is not None and lng is not None:
        point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326).cast(Geography)
        within_50m = func.ST_DWithin(Place.location, point, 50).label("within_50m")

    stmt = select(Place, name_similarity, within_50m)

    conditions = [name_similarity >= 0.6]
    if normalized_phone:
        normalized_phone_expr = func.regexp_replace(Place.phone, r"\D", "", "g")
        conditions.append(normalized_phone_expr == normalized_phone)
    if point is not None:
        conditions.append(func.ST_DWithin(Place.location, point, 50))

    stmt = stmt.where(or_(*conditions))
    if exclude_place_id:
        stmt = stmt.where(Place.id != exclude_place_id)

    rows = (await db.execute(stmt)).all()

    candidates: list[DuplicateCandidate] = []
    for place, sim, is_near in rows:
        score = 0.0
        has_strong_signal = False
        reasons: list[str] = []

        if sim and sim >= 0.6:
            score += min(float(sim), 1.0) * 0.3
            reasons.append(f"name_similarity={sim:.2f}")
            if sim >= 0.95:
                score += 0.4
                reasons.append("high_name_similarity_bonus")
                has_strong_signal = True

        if normalized_phone and place.phone and normalize_phone(place.phone) == normalized_phone:
            score += 0.4
            reasons.append("phone_match")
            has_strong_signal = True

        if bool(is_near):
            score += 0.3
            reasons.append("within_50m")

        if score >= 0.7 or has_strong_signal:
            candidates.append(
                DuplicateCandidate(
                    place_id=place.id,
                    canonical_name=place.canonical_name,
                    score=round(score, 3),
                    reasons=reasons,
                )
            )

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates


async def merge_places(db: AsyncSession, keep_id: uuid.UUID, merge_id: uuid.UUID) -> Place | None:
    """Merge duplicate place data into keep_id and delete merge_id."""
    if keep_id == merge_id:
        raise ValueError("keep_id and merge_id must be different")

    keep_place = await db.get(Place, keep_id)
    merge_place = await db.get(Place, merge_id)

    if keep_place is None or merge_place is None:
        return None

    keep_tag_ids_subquery = select(PlaceTag.tag_id).where(PlaceTag.place_id == keep_id)

    await db.execute(
        delete(PlaceTag).where(PlaceTag.place_id == merge_id).where(PlaceTag.tag_id.in_(keep_tag_ids_subquery))
    )

    for model in (ProviderLink, Source, Note, Visit, Media):
        await db.execute(update(model).where(model.place_id == merge_id).values(place_id=keep_id))

    await db.execute(update(PlaceTag).where(PlaceTag.place_id == merge_id).values(place_id=keep_id))

    await db.delete(merge_place)

    db.add(
        AuditLog(
            action="merge",
            entity_type="place",
            entity_id=keep_id,
            detail={"keep_id": str(keep_id), "merge_id": str(merge_id)},
        )
    )

    await db.commit()

    stmt = (
        select(Place)
        .options(
            selectinload(Place.provider_links),
            selectinload(Place.tags),
            selectinload(Place.sources),
            selectinload(Place.notes),
            selectinload(Place.visits),
        )
        .where(Place.id == keep_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()
