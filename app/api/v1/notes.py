"""Note API routes with authentication and validation."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, require_auth
from app.models.user import User
from app.schemas.note import (
    NoteCreate, NoteUpdate, NoteResponse, 
    NoteListResponse, NoteSearchQuery
)
from app.services.note import NoteService

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.get("", response_model=NoteListResponse)
async def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_archived: Optional[bool] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    category_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated notes with filtering."""
    service = NoteService(db)
    notes, total = service.repository.get_by_user(
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        is_archived=is_archived,
        is_pinned=is_pinned,
        category_id=category_id
    )
    
    return {
        "items": [note.to_dict() for note in notes],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new note."""
    service = NoteService(db)
    note = service.create_note(str(current_user.id), note_data)
    return note.to_dict()


@router.get("/search", response_model=NoteListResponse)
async def search_notes(
    q: str = Query(..., min_length=1, max_length=200),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full-text search notes."""
    service = NoteService(db)
    notes, total = service.repository.search_notes(
        user_id=str(current_user.id),
        query=q,
        skip=skip,
        limit=limit
    )
    
    return {
        "items": [note.to_dict() for note in notes],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/pinned", response_model=List[NoteResponse])
async def get_pinned_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pinned notes."""
    service = NoteService(db)
    notes = service.repository.get_pinned_by_user(str(current_user.id))
    return [note.to_dict() for note in notes]


@router.get("/archived", response_model=NoteListResponse)
async def get_archived_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get archived notes."""
    service = NoteService(db)
    notes, total = service.repository.get_archived_by_user(
        user_id=str(current_user.id),
        skip=skip,
        limit=limit
    )
    
    return {
        "items": [note.to_dict() for note in notes],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single note by ID."""
    service = NoteService(db)
    note = service.repository.get_with_relations(note_id)
    
    if not note or str(note.user_id) != str(current_user.id):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Note not found")
    
    return note.to_dict(include_content=True)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a note."""
    service = NoteService(db)
    note = service.update_note(str(current_user.id), note_id, note_data)
    return note.to_dict(include_content=True)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a note."""
    service = NoteService(db)
    service.delete_note(str(current_user.id), note_id)
    return None


@router.post("/{note_id}/pin", response_model=NoteResponse)
async def pin_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pin a note."""
    service = NoteService(db)
    note = service.pin_note(str(current_user.id), note_id)
    return note.to_dict()


@router.post("/{note_id}/unpin", response_model=NoteResponse)
async def unpin_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unpin a note."""
    service = NoteService(db)
    note = service.update_note(str(current_user.id), note_id, {"is_pinned": False})
    return note.to_dict()


@router.post("/{note_id}/archive", response_model=NoteResponse)
async def archive_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a note."""
    service = NoteService(db)
    note = service.archive_note(str(current_user.id), note_id)
    return note.to_dict()


@router.post("/{note_id}/unarchive", response_model=NoteResponse)
async def unarchive_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unarchive a note."""
    service = NoteService(db)
    note = service.update_note(str(current_user.id), note_id, {"is_archived": False})
    return note.to_dict()
