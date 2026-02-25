"""SQLAlchemy ORM 모델 — Base 및 전체 모델 re-export."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Alembic autogenerate가 모든 모델을 인식하도록 import 유지
from app.models.audit import AuditLog, CostLog  # noqa: E402, F401
from app.models.embedding import Embedding  # noqa: E402, F401
from app.models.media import Media  # noqa: E402, F401
from app.models.note import Note  # noqa: E402, F401
from app.models.ontology import OntologyNode, Relation  # noqa: E402, F401
from app.models.place import Place, ProviderLink  # noqa: E402, F401
from app.models.source import Source  # noqa: E402, F401
from app.models.tag import PlaceTag, Tag  # noqa: E402, F401
from app.models.visit import Visit  # noqa: E402, F401
