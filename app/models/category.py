"""Category model for organizing notes hierarchically."""
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.note import Note


class Category(Base, UUIDMixin, TimestampMixin):
    """
    Category model for organizing notes hierarchically.
    
    Attributes:
        user_id: Foreign key to category owner
        name: Category name (max 50 characters)
        color: Hex color code for UI display
        icon: Optional icon identifier
        parent_id: Self-referential FK for hierarchy
        user: Relationship to owner
        notes: Relationship to notes in category
        parent: Parent category
        children: Sub-categories
    """
    
    __tablename__ = "categories"
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Content fields
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    color: Mapped[str] = mapped_column(
        String(7),
        default="#6366f1",
        nullable=False
    )
    icon: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="categories")
    notes: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="category",
        lazy="dynamic"
    )
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        Index('ix_categories_user_name', 'user_id', 'name', unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, user_id={self.user_id})>"
    
    def get_full_path(self) -> str:
        """Get full hierarchical path of category names."""
        if self.parent is None:
            return self.name
        return f"{self.parent.get_full_path()} / {self.name}"
    
    def get_descendants(self) -> List["Category"]:
        """Get all descendant categories recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
