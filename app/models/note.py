"""Note model for storing user notes with markdown content."""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category
    from app.models.tag import Tag


class Note(Base, UUIDMixin, TimestampMixin):
    """
    Note model for storing user notes with markdown content.
    
    Attributes:
        user_id: Foreign key to the note owner
        category_id: Optional foreign key to category
        title: Note title (max 200 characters)
        content: Markdown content (unlimited length)
        is_pinned: Whether note is pinned to top
        is_archived: Whether note is archived
        pinned_at: Timestamp when note was pinned
        archived_at: Timestamp when note was archived
        search_vector: PostgreSQL full-text search vector
        user: Relationship to note owner
        category: Relationship to category
        tags: Many-to-many relationship to tags
    """
    
    __tablename__ = "notes"
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Content fields
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=""
    )
    
    # Status fields
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # Timestamp fields for status changes
    pinned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Full-text search vector
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notes")
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="notes"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary="note_tags",
        back_populates="notes",
        lazy="selectin"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_notes_user_created', 'user_id', 'created_at'),
        Index('ix_notes_search', 'search_vector', postgresql_using='gin'),
    )
    
    def __repr__(self) -> str:
        return f"<Note(id={self.id}, title={self.title[:50]}, user_id={self.user_id})>"
    
    def pin(self) -> None:
        """Pin the note to the top."""
        self.is_pinned = True
        self.pinned_at = datetime.utcnow()
    
    def unpin(self) -> None:
        """Unpin the note."""
        self.is_pinned = False
        self.pinned_at = None
    
    def archive(self) -> None:
        """Archive the note."""
        self.is_archived = True
        self.archived_at = datetime.utcnow()
    
    def unarchive(self) -> None:
        """Unarchive the note."""
        self.is_archived = False
        self.archived_at = None
