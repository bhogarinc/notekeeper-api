"""Pydantic schemas for User model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.base import BaseSchema


# ============== Request Schemas ==============

class UserCreate(BaseModel):
    """Schema for user registration."""
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Unique username (alphanumeric and underscores only)",
        examples=["john_doe"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)",
        examples=["SecurePass123!"]
    )


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    
    email: Optional[EmailStr] = Field(
        None,
        description="New email address"
    )
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Schema for password change."""
    
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128
    )


# ============== Response Schemas ==============

class UserResponse(BaseSchema):
    """Schema for user response (public data)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class UserProfileResponse(UserResponse):
    """Extended user response with additional profile data."""
    
    note_count: int = Field(0, description="Total number of notes")
    category_count: int = Field(0, description="Total number of categories")
    tag_count: int = Field(0, description="Total number of tags")
