"""Pydantic schemas for Tag model."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.base import BaseSchema


class TagCreate(BaseModel):
    """Schema for creating a tag."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        examples=["important"]
    )
    color: str = Field(
        default="#10b981",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        examples=["#10b981"]
    )


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=30)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseSchema):
    """Tag response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    color: str
    created_at: datetime
    updated_at: datetime
    note_count: int = Field(0, description="Number of notes with this tag")
