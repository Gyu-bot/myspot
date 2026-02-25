"""Ontology models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class OntologyNode(Base):
    """Ontology tree node."""

    __tablename__ = "ontology_nodes"
    __table_args__ = (
        CheckConstraint(
            "namespace IN ('cuisine', 'mood', 'situation', 'companion', 'feature')",
            name="ck_ontology_nodes_namespace",
        ),
        UniqueConstraint("name", "namespace", name="uq_ontology_nodes_name_namespace"),
        Index("idx_ontology_parent", "parent_id"),
        Index("idx_ontology_namespace", "namespace"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    namespace: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ontology_nodes.id"))

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

    parent: Mapped[OntologyNode | None] = relationship(remote_side="OntologyNode.id", backref="children")


class Relation(Base):
    """Generic relation model between entities."""

    __tablename__ = "relations"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_relations_confidence"),
        Index("idx_relations_from", "from_entity_type", "from_entity_id"),
        Index("idx_relations_to", "to_entity_type", "to_entity_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    from_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    to_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, server_default=text("1.0"))
    evidence_source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))

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
