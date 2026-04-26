"""Pydantic schemas for Category model."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.base import BaseSchema


class CategoryCreate(BaseModel):
    """Schema for creating a category."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["Work"]
    )
    color: str = Field(
        default="#6366f1",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        examples=["#6366f1"]
    )
    icon: Optional[str] = Field(
        None,
        max_length=50,
        examples=["briefcase"]
    )
    parent_id: Optional[UUID] = None


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[UUID] = None


class CategoryResponse(BaseSchema):
    """Category response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    color: str
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    note_count: int = Field(0, description="Number of notes in category")
    full_path: str = Field("", description="Full hierarchical path")


class CategoryTreeResponse(CategoryResponse):
    """Category response with children."""
    
    children: List["CategoryTreeResponse"] = []
