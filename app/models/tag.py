"""Tag model for labeling notes with keywords."""
from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy import ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.note import Note


class Tag(Base, UUIDMixin, TimestampMixin):
    """
    Tag model for labeling notes with keywords.
    
    Attributes:
        user_id: Foreign key to tag owner
        name: Tag name (max 30 characters)
        color: Hex color code for UI display
        user: Relationship to owner
        notes: Many-to-many relationship to notes
    """
    
    __tablename__ = "tags"
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Content fields
    name: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    color: Mapped[str] = mapped_column(
        String(7),
        default="#10b981",
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tags")
    notes: Mapped[List["Note"]] = relationship(
        "Note",
        secondary="note_tags",
        back_populates="tags",
        lazy="dynamic"
    )
    
    # Table constraints
    __table_args__ = (
        Index('ix_tags_user_name', 'user_id', 'name', unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name}, user_id={self.user_id})>"
    
    @property
    def note_count(self) -> int:
        """Get count of notes with this tag."""
        return self.notes.count()
