"""Tags API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.tag import Tag
from app.models.user import User
from app.schemas.common import ErrorResponse, ErrorDetail, SuccessResponse, PaginatedResponse
from app.schemas.tag import TagCreate, TagUpdate, TagResponse

router = APIRouter()


def get_tag_or_404(db: Session, tag_id: int, user_id: int) -> Tag:
    """Get tag by ID or raise 404."""
    tag = db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.user_id == user_id
    ).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="Tag not found"
                )
            ).model_dump()
        )
    return tag


@router.get(
    "/",
    response_model=SuccessResponse[PaginatedResponse[TagResponse]],
    summary="List tags",
    description="Get all user's tags with note counts."
)
async def list_tags(
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[PaginatedResponse[TagResponse]]:
    """
    List all tags for the current user.
    
    - **search**: Filter tags by name (case-insensitive partial match)
    """
    query = db.query(Tag).filter(Tag.user_id == current_user.id)
    
    if search:
        query = query.filter(Tag.name.ilike(f"%{search}%"))
    
    query = query.order_by(Tag.name.asc())
    
    tags = query.all()
    
    # Add note counts
    tag_items = []
    for tag in tags:
        tag_data = TagResponse.model_validate(tag)
        tag_data.notes_count = len(tag.notes)
        tag_items.append(tag_data)
    
    # Simple pagination for tags (usually not many)
    paginated = PaginatedResponse[TagResponse](
        items=tag_items,
        total=len(tag_items),
        page=1,
        page_size=len(tag_items) or 1,
        pages=1
    )
    
    return SuccessResponse(data=paginated)


@router.post(
    "/",
    response_model=SuccessResponse[TagResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
    description="Create a new tag."
)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[TagResponse]:
    """
    Create a new tag.
    
    Tag names must be unique per user (case-insensitive).
    """
    # Check for duplicate name
    existing = db.query(Tag).filter(
        Tag.user_id == current_user.id,
        func.lower(Tag.name) == func.lower(tag_data.name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="DUPLICATE_NAME",
                    message="Tag with this name already exists",
                    field="name"
                )
            ).model_dump()
        )
    
    tag = Tag(
        name=tag_data.name,
        color=tag_data.color,
        user_id=current_user.id
    )
    
    db.add(tag)
    db.commit()
    db.refresh(tag)
    
    return SuccessResponse(
        data=TagResponse.model_validate(tag),
        message="Tag created successfully"
    )


@router.get(
    "/{tag_id}",
    response_model=SuccessResponse[TagResponse],
    summary="Get tag",
    description="Get a single tag by ID."
)
async def get_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[TagResponse]:
    """Get a specific tag with its note count."""
    tag = get_tag_or_404(db, tag_id, current_user.id)
    
    tag_data = TagResponse.model_validate(tag)
    tag_data.notes_count = len(tag.notes)
    
    return SuccessResponse(data=tag_data)


@router.patch(
    "/{tag_id}",
    response_model=SuccessResponse[TagResponse],
    summary="Update tag",
    description="Update an existing tag."
)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[TagResponse]:
    """Update a tag's details."""
    tag = get_tag_or_404(db, tag_id, current_user.id)
    
    update_dict = tag_data.model_dump(exclude_unset=True)
    
    # Check for duplicate name if updating name
    if "name" in update_dict:
        existing = db.query(Tag).filter(
            Tag.user_id == current_user.id,
            func.lower(Tag.name) == func.lower(update_dict["name"]),
            Tag.id != tag_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="DUPLICATE_NAME",
                        message="Tag with this name already exists",
                        field="name"
                    )
                ).model_dump()
            )
    
    for field, value in update_dict.items():
        setattr(tag, field, value)
    
    db.commit()
    db.refresh(tag)
    
    return SuccessResponse(
        data=TagResponse.model_validate(tag),
        message="Tag updated successfully"
    )


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
    description="Delete a tag. Notes will lose this tag."
)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a tag.
    
    The tag will be removed from all associated notes.
    """
    tag = get_tag_or_404(db, tag_id, current_user.id)
    
    # Tag will be removed from notes via association table cascade
    db.delete(tag)
    db.commit()
