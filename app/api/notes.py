"""Notes API routes."""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.api.deps import get_db, get_current_user
from app.models.note import Note
from app.models.tag import Tag
from app.models.user import User
from app.schemas.common import (
    ErrorResponse, ErrorDetail, SuccessResponse,
    PaginationParams, PaginatedResponse
)
from app.schemas.note import (
    NoteCreate, NoteUpdate, NoteResponse, NoteListResponse,
    NoteSearchQuery, NoteBulkAction
)

router = APIRouter()


def get_note_or_404(db: Session, note_id: int, user_id: int) -> Note:
    """Get note by ID or raise 404."""
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == user_id
    ).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="Note not found"
                )
            ).model_dump()
        )
    return note


@router.get(
    "/",
    response_model=SuccessResponse[PaginatedResponse[NoteListResponse]],
    summary="List notes",
    description="Get paginated list of user's notes with filtering options."
)
async def list_notes(
    q: Optional[str] = Query(None, description="Search query"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    tag_ids: Optional[List[int]] = Query(None, description="Filter by tags"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[PaginatedResponse[NoteListResponse]]:
    """
    List user's notes with optional filtering and sorting.
    
    - **q**: Full-text search in title and content
    - **category_id**: Filter by category
    - **tag_ids**: Filter by tags (notes must have all specified tags)
    - **is_pinned**: Filter pinned/unpinned notes
    - **is_archived**: Filter archived/unarchived notes
    """
    query = db.query(Note).filter(Note.user_id == current_user.id)
    
    # Apply filters
    if q:
        search_filter = or_(
            Note.title.ilike(f"%{q}%"),
            Note.content.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    
    if category_id is not None:
        query = query.filter(Note.category_id == category_id)
    
    if is_pinned is not None:
        query = query.filter(Note.is_pinned == is_pinned)
    
    if is_archived is not None:
        query = query.filter(Note.is_archived == is_archived)
    else:
        # By default, exclude archived notes
        query = query.filter(Note.is_archived == False)
    
    # Filter by tags
    if tag_ids:
        for tag_id in tag_ids:
            query = query.filter(Note.tags.any(Tag.id == tag_id))
    
    # Apply sorting
    sort_column = getattr(Note, sort_by, Note.updated_at)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(Note.is_pinned.desc(), sort_column)
    
    # Execute query
    total = query.count()
    notes = query.offset(pagination.offset).limit(pagination.page_size).all()
    
    # Build response
    note_items = []
    for note in notes:
        preview = note.content[:200] + "..." if len(note.content) > 200 else note.content
        note_items.append(NoteListResponse(
            id=note.id,
            title=note.title,
            content_preview=preview,
            is_pinned=note.is_pinned,
            is_archived=note.is_archived,
            color=note.color,
            category_name=note.category.name if note.category else None,
            tags=[tag.name for tag in note.tags],
            created_at=note.created_at,
            updated_at=note.updated_at
        ))
    
    pages = (total + pagination.page_size - 1) // pagination.page_size
    
    paginated = PaginatedResponse[NoteListResponse](
        items=note_items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages
    )
    
    return SuccessResponse(data=paginated)


@router.post(
    "/",
    response_model=SuccessResponse[NoteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Create a new note with optional category and tags."
)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[NoteResponse]:
    """
    Create a new note.
    
    - Category and tags are optional
    - Tags are matched by ID and must belong to the user
    """
    # Validate category belongs to user
    if note_data.category_id:
        from app.models.category import Category
        category = db.query(Category).filter(
            Category.id == note_data.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="INVALID_CATEGORY",
                        message="Category not found",
                        field="category_id"
                    )
                ).model_dump()
            )
    
    # Create note
    note = Note(
        title=note_data.title,
        content=note_data.content,
        is_pinned=note_data.is_pinned,
        is_archived=note_data.is_archived,
        color=note_data.color,
        category_id=note_data.category_id,
        user_id=current_user.id
    )
    
    # Add tags
    if note_data.tag_ids:
        tags = db.query(Tag).filter(
            Tag.id.in_(note_data.tag_ids),
            Tag.user_id == current_user.id
        ).all()
        note.tags = tags
    
    db.add(note)
    db.commit()
    db.refresh(note)
    
    return SuccessResponse(
        data=NoteResponse.model_validate(note),
        message="Note created successfully"
    )


@router.get(
    "/{note_id}",
    response_model=SuccessResponse[NoteResponse],
    summary="Get note",
    description="Get a single note by ID."
)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[NoteResponse]:
    """Get detailed information about a specific note."""
    note = get_note_or_404(db, note_id, current_user.id)
    
    # Render markdown to HTML
    import markdown
    from bs4 import BeautifulSoup
    
    html_content = markdown.markdown(
        note.content,
        extensions=['fenced_code', 'tables', 'toc']
    )
    
    # Calculate word count
    soup = BeautifulSoup(note.content, 'html.parser')
    text = soup.get_text()
    word_count = len(text.split())
    
    response_data = NoteResponse.model_validate(note)
    response_data.html_content = html_content
    response_data.word_count = word_count
    
    return SuccessResponse(data=response_data)


@router.patch(
    "/{note_id}",
    response_model=SuccessResponse[NoteResponse],
    summary="Update note",
    description="Update an existing note."
)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[NoteResponse]:
    """
    Update a note.
    
    Only provided fields are updated. To remove category, set category_id to null.
    """
    note = get_note_or_404(db, note_id, current_user.id)
    
    update_dict = note_data.model_dump(exclude_unset=True)
    
    # Handle category update
    if "category_id" in update_dict:
        category_id = update_dict["category_id"]
        if category_id is not None:
            from app.models.category import Category
            category = db.query(Category).filter(
                Category.id == category_id,
                Category.user_id == current_user.id
            ).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error=ErrorDetail(
                            code="INVALID_CATEGORY",
                            message="Category not found",
                            field="category_id"
                        )
                    ).model_dump()
                )
    
    # Handle tags update
    if "tag_ids" in update_dict:
        tag_ids = update_dict.pop("tag_ids")
        if tag_ids is not None:
            tags = db.query(Tag).filter(
                Tag.id.in_(tag_ids),
                Tag.user_id == current_user.id
            ).all()
            note.tags = tags
    
    # Update note fields
    for field, value in update_dict.items():
        setattr(note, field, value)
    
    db.commit()
    db.refresh(note)
    
    return SuccessResponse(
        data=NoteResponse.model_validate(note),
        message="Note updated successfully"
    )


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete note",
    description="Permanently delete a note."
)
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """Delete a note permanently."""
    note = get_note_or_404(db, note_id, current_user.id)
    db.delete(note)
    db.commit()


@router.post(
    "/{note_id}/pin",
    response_model=SuccessResponse[NoteResponse],
    summary="Toggle pin status",
    description="Pin or unpin a note."
)
async def toggle_pin(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[NoteResponse]:
    """Toggle the pinned status of a note."""
    note = get_note_or_404(db, note_id, current_user.id)
    note.is_pinned = not note.is_pinned
    db.commit()
    db.refresh(note)
    
    action = "pinned" if note.is_pinned else "unpinned"
    return SuccessResponse(
        data=NoteResponse.model_validate(note),
        message=f"Note {action} successfully"
    )


@router.post(
    "/{note_id}/archive",
    response_model=SuccessResponse[NoteResponse],
    summary="Toggle archive status",
    description="Archive or unarchive a note."
)
async def toggle_archive(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[NoteResponse]:
    """Toggle the archived status of a note."""
    note = get_note_or_404(db, note_id, current_user.id)
    note.is_archived = not note.is_archived
    
    # Unpin archived notes
    if note.is_archived:
        note.is_pinned = False
    
    db.commit()
    db.refresh(note)
    
    action = "archived" if note.is_archived else "unarchived"
    return SuccessResponse(
        data=NoteResponse.model_validate(note),
        message=f"Note {action} successfully"
    )


@router.post(
    "/bulk",
    response_model=SuccessResponse[dict],
    summary="Bulk action on notes",
    description="Perform bulk actions (archive, pin, delete) on multiple notes."
)
async def bulk_action(
    action_data: NoteBulkAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[dict]:
    """
    Perform bulk actions on multiple notes.
    
    Actions: archive, unarchive, pin, unpin, delete
    """
    query = db.query(Note).filter(
        Note.id.in_(action_data.note_ids),
        Note.user_id == current_user.id
    )
    
    notes = query.all()
    affected_count = len(notes)
    
    if action_data.action == "delete":
        for note in notes:
            db.delete(note)
    elif action_data.action == "archive":
        for note in notes:
            note.is_archived = True
            note.is_pinned = False
    elif action_data.action == "unarchive":
        for note in notes:
            note.is_archived = False
    elif action_data.action == "pin":
        for note in notes:
            if not note.is_archived:
                note.is_pinned = True
    elif action_data.action == "unpin":
        for note in notes:
            note.is_pinned = False
    
    db.commit()
    
    return SuccessResponse(
        data={"affected": affected_count},
        message=f"Bulk {action_data.action} completed on {affected_count} notes"
    )
