"""User model for authentication and note ownership."""
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.note import Note
    from app.models.category import Category
    from app.models.tag import Tag


class User(Base, UUIDMixin, TimestampMixin):
    """
    User model for authentication and note ownership.
    
    Attributes:
        email: Unique email address for the user
        username: Unique username for display
        password_hash: Bcrypt hashed password
        is_active: Whether the account is active
        is_verified: Whether email is verified
        failed_login_attempts: Counter for account lockout
        locked_until: Timestamp when account unlocks
        last_login: Timestamp of last successful login
        notes: Relationship to user's notes
        categories: Relationship to user's categories
        tags: Relationship to user's tags
    """
    
    __tablename__ = "users"
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Security fields
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    notes: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    def is_locked(self) -> bool:
        """Check if user account is currently locked."""
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.utcnow()
    
    def increment_failed_login(self) -> None:
        """Increment failed login attempts and lock if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_login(self) -> None:
        """Reset failed login attempts on successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()
