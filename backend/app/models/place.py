"""Place and ProviderLink models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.media import Media
    from app.models.note import Note
    from app.models.source import Source
    from app.models.tag import Tag
    from app.models.visit import Visit


class Place(Base):
    """Canonical place entity."""

    __tablename__ = "places"
    __table_args__ = (
        CheckConstraint(
            "reservation IN ('available', 'required', 'unavailable', 'unknown')",
            name="ck_places_reservation",
        ),
        CheckConstraint(
            "price_range IN ('cheap', 'moderate', 'expensive', 'very_expensive', 'unknown')",
            name="ck_places_price_range",
        ),
        CheckConstraint("user_rating BETWEEN 1 AND 5", name="ck_places_user_rating"),
        Index(
            "idx_places_normalized_name",
            "normalized_name",
            postgresql_using="gin",
            postgresql_ops={"normalized_name": "gin_trgm_ops"},
        ),
        Index("idx_places_location", "location", postgresql_using="gist"),
        Index("idx_places_category", "category_primary", "category_secondary"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)

    address_road: Mapped[str | None] = mapped_column(Text)
    address_jibun: Mapped[str | None] = mapped_column(Text)
    region_depth1: Mapped[str | None] = mapped_column(Text)
    region_depth2: Mapped[str | None] = mapped_column(Text)
    region_depth3: Mapped[str | None] = mapped_column(Text)

    location: Mapped[WKBElement | None] = mapped_column(Geography("POINT", srid=4326, spatial_index=False))
    phone: Mapped[str | None] = mapped_column(String(32))

    category_primary: Mapped[str | None] = mapped_column(Text)
    category_secondary: Mapped[str | None] = mapped_column(Text)

    parking: Mapped[bool | None] = mapped_column(Boolean)
    reservation: Mapped[str | None] = mapped_column(String(32))
    price_range: Mapped[str | None] = mapped_column(String(32))

    mood: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    companions: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    situations: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    user_rating: Mapped[int | None] = mapped_column(SmallInteger)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    provider_links: Mapped[list[ProviderLink]] = relationship(back_populates="place", cascade="all, delete-orphan")
    sources: Mapped[list[Source]] = relationship(back_populates="place", cascade="all, delete-orphan")
    notes: Mapped[list[Note]] = relationship(back_populates="place", cascade="all, delete-orphan")
    visits: Mapped[list[Visit]] = relationship(back_populates="place", cascade="all, delete-orphan")
    media: Mapped[list[Media]] = relationship(back_populates="place", cascade="all, delete-orphan")

    tags: Mapped[list[Tag]] = relationship(
        secondary="place_tags",
        back_populates="places",
        lazy="selectin",
    )


class ProviderLink(Base):
    """External provider link for a place."""

    __tablename__ = "provider_links"
    __table_args__ = (
        CheckConstraint("provider IN ('NAVER', 'KAKAO', 'GOOGLE', 'ETC')", name="ck_provider_links_provider"),
        UniqueConstraint("place_id", "provider", name="uq_provider_links_place_provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    place_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("places.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_place_id: Mapped[str | None] = mapped_column(Text)
    provider_url: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    place: Mapped[Place] = relationship(back_populates="provider_links")
