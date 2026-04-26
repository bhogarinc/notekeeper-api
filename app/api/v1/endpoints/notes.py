"""
Notes API endpoints for NoteKeeper.

This module implements REST API endpoints for note management including
CRUD operations, search, filtering, pinning, and archiving.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteSummaryResponse,
    NoteUpdate,
    NoteSearchParams,
    NoteStatusUpdate,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.models.user import User
from app.services.note import NoteService


router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[NoteSummaryResponse],
    summary="List notes",
    description="Get paginated list of notes with optional filtering and sorting.",
)
async def list_notes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Full-text search query"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    tag_ids: Optional[list[UUID]] = Query(None, description="Filter by tags"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    is_archived: bool = Query(False, description="Include archived notes"),
    sort_by: str = Query("updated_at", regex="^(updated_at|created_at|title)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[NoteSummaryResponse]:
    """
    List notes with pagination and filtering.
    
    - **search**: Full-text search in title and content
    - **category_id**: Filter by category UUID
    - **tag_ids**: Filter by tags (notes must have all specified tags)
    - **is_pinned**: Filter by pinned status
    - **is_archived**: Include archived notes (default: false)
    - **sort_by**: Sort field (updated_at, created_at, title)
    - **sort_order**: Sort direction (asc, desc)
    - **page**: Page number (1-indexed)
    - **limit**: Items per page (max 100)
    """
    service = NoteService(db)
    
    filters = NoteSearchParams(
        q=search,
        category_id=category_id,
        tag_ids=tag_ids,
        is_pinned=is_pinned,
        is_archived=is_archived,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
    )
    
    pagination = PaginationParams(page=page, limit=limit)
    
    notes, total = await service.list_notes(
        user_id=current_user.id,
        filters=filters,
        pagination=pagination,
    )
    
    return PaginatedResponse.create(items=notes, params=pagination, total=total)


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Create a new note with optional category and tags.",
)
async def create_note(
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    """
    Create a new note.
    
    - **title**: Note title (required, max 200 chars)
    - **content**: Markdown content
    - **category_id**: Optional category UUID
    - **tag_ids**: Optional list of tag UUIDs
    - **is_pinned**: Whether to pin the note
    """
    service = NoteService(db)
    note = await service.create_note(
        user_id=current_user.id,
        note_data=note_in,
    )
    return note


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get note",
    description="Get a single note by ID.",
)
async def get_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    """
    Get a note by ID.
    
    - **note_id**: UUID of the note to retrieve
    """
    service = NoteService(db)
    note = await service.get_note_by_id(
        note_id=note_id,
        user_id=current_user.id,
    )
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    
    return note


@router.patch(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update note",
    description="Update an existing note. Only provided fields are updated.",
)
async def update_note(
    note_id: UUID,
    note_in: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    """
    Update a note.
    
    - **note_id**: UUID of the note to update
    - **title**: New title (optional)
    - **content**: New content (optional)
    - **category_id**: New category (optional, null to remove)
    - **tag_ids**: Replace tags (optional)
    """
    service = NoteService(db)
    note = await service.update_note(
        note_id=note_id,
        user_id=current_user.id,
        note_data=note_in,
    )
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    
    return note


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete note",
    description="Delete a note permanently.",
)
async def delete_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a note.
    
    - **note_id**: UUID of the note to delete
    """
    service = NoteService(db)
    deleted = await service.delete_note(
        note_id=note_id,
        user_id=current_user.id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )


@router.patch(
    "/{note_id}/pin",
    response_model=NoteResponse,
    summary="Toggle pin",
    description="Pin or unpin a note.",
)
async def toggle_pin(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    """
    Toggle the pinned status of a note.
    
    - **note_id**: UUID of the note to pin/unpin
    """
    service = NoteService(db)
    note = await service.toggle_pin(
        note_id=note_id,
        user_id=current_user.id,
    )
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    
    return note


@router.patch(
    "/{note_id}/archive",
    response_model=NoteResponse,
    summary="Toggle archive",
    description="Archive or unarchive a note.",
)
async def toggle_archive(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    """
    Toggle the archived status of a note.
    
    - **note_id**: UUID of the note to archive/unarchive
    """
    service = NoteService(db)
    note = await service.toggle_archive(
        note_id=note_id,
        user_id=current_user.id,
    )
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    
    return note


@router.get(
    "/search",
    response_model=PaginatedResponse[NoteSummaryResponse],
    summary="Search notes",
    description="Full-text search across note titles and content.",
)
async def search_notes(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[NoteSummaryResponse]:
    """
    Search notes using full-text search.
    
    - **q**: Search query (required, min 1 character)
    - **page**: Page number (1-indexed)
    - **limit**: Items per page (max 100)
    """
    service = NoteService(db)
    pagination = PaginationParams(page=page, limit=limit)
    
    notes, total = await service.search_notes(
        user_id=current_user.id,
        query=q,
        pagination=pagination,
    )
    
    return PaginatedResponse.create(items=notes, params=pagination, total=total)
