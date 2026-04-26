"""Association table for Note-Tag many-to-many relationship."""
from uuid import UUID

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base


# Association table for Note-Tag many-to-many relationship
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column(
        "note_id",
        PG_UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "tag_id",
        PG_UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True
    )
)
