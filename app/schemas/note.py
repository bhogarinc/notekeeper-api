"""Pydantic schemas for Note model."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.base import BaseSchema
from app.schemas.tag import TagResponse


# ============== Request Schemas ==============

class NoteCreate(BaseModel):
    """Schema for creating a new note."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Note title",
        examples=["My Important Note"]
    )
    content: str = Field(
        default="",
        description="Note content in Markdown format",
        examples=["# Heading\n\nThis is the note content."]
    )
    category_id: Optional[UUID] = Field(
        None,
        description="Optional category ID"
    )
    tag_ids: List[UUID] = Field(
        default=[],
        description="List of tag IDs to attach"
    )
    is_pinned: bool = Field(
        default=False,
        description="Whether to pin the note"
    )


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200
    )
    content: Optional[str] = None
    category_id: Optional[UUID] = None
    tag_ids: Optional[List[UUID]] = None


class NoteStatusUpdate(BaseModel):
    """Schema for updating note status (pin/archive)."""
    
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


# ============== Response Schemas ==============

class NoteSummaryResponse(BaseSchema):
    """Lightweight note response for list views."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None
    tag_count: int = Field(0, description="Number of tags")
    content_preview: str = Field(
        "",
        max_length=200,
        description="First 200 characters of content"
    )


class NoteResponse(BaseSchema):
    """Full note response with all details."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    content: str
    is_pinned: bool
    is_archived: bool
    pinned_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    tags: List[TagResponse] = []


# ============== Search/Filter Schemas ==============

class NoteSearchParams(BaseModel):
    """Query parameters for note search."""
    
    q: Optional[str] = Field(
        None,
        description="Search query for title and content"
    )
    category_id: Optional[UUID] = None
    tag_ids: Optional[List[UUID]] = Field(None, description="Filter by tags (AND logic)")
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = Field(False, description="Include archived notes")
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = Field(default="updated_at", pattern="^(created_at|updated_at|title)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    cursor: Optional[str] = Field(None, description="Pagination cursor")
    limit: int = Field(default=20, ge=1, le=100)
