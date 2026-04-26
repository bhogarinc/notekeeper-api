"""User management API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.common import (
    ErrorResponse, ErrorDetail, SuccessResponse,
    PaginationParams, PaginatedResponse
)
from app.schemas.user import UserResponse, UserUpdate, UserProfileResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=SuccessResponse[UserProfileResponse],
    summary="Get current user profile",
    description="Returns the authenticated user's profile with statistics.",
    responses={
        200: {"description": "Profile retrieved"},
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[UserProfileResponse]:
    """
    Get detailed profile of the current authenticated user.
    
    Includes statistics like notes count, categories count, etc.
    """
    # Calculate statistics
    notes_count = len(current_user.notes)
    pinned_count = sum(1 for n in current_user.notes if n.is_pinned)
    archived_count = sum(1 for n in current_user.notes if n.is_archived)
    
    profile_data = UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        notes_count=notes_count,
        categories_count=len(current_user.categories),
        tags_count=len(current_user.tags),
        pinned_notes_count=pinned_count,
        archived_notes_count=archived_count
    )
    
    return SuccessResponse(data=profile_data)


@router.patch(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Update current user",
    description="Update the authenticated user's profile information.",
    responses={
        200: {"description": "Profile updated"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Email already exists"}
    }
)
async def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[UserResponse]:
    """
    Update current user's profile.
    
    Only provided fields are updated. Email change requires uniqueness check.
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Check email uniqueness if updating email
    if "email" in update_dict and update_dict["email"] != current_user.email:
        existing = db.query(User).filter(
            User.email == update_dict["email"],
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="EMAIL_EXISTS",
                        message="Email address already in use",
                        field="email"
                    )
                ).model_dump()
            )
    
    # Hash password if updating
    if "password" in update_dict:
        update_dict["hashed_password"] = get_password_hash(update_dict.pop("password"))
    
    # Update fields
    for field, value in update_dict.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return SuccessResponse(
        data=UserResponse.model_validate(current_user),
        message="Profile updated successfully"
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user",
    description="Permanently delete the authenticated user's account.",
    responses={
        204: {"description": "Account deleted"},
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete the current user's account and all associated data.
    
    This action is irreversible.
    """
    db.delete(current_user)
    db.commit()


@router.get(
    "/",
    response_model=SuccessResponse[PaginatedResponse[UserResponse]],
    summary="List users (admin)",
    description="List all users with pagination (admin only).",
    responses={
        200: {"description": "Users list retrieved"},
        403: {"model": ErrorResponse, "description": "Admin access required"}
    }
)
async def list_users(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[PaginatedResponse[UserResponse]]:
    """
    List all users with pagination.
    
    Requires admin privileges (placeholder - implement proper admin check).
    """
    # TODO: Add proper admin role check
    
    query = db.query(User).order_by(User.created_at.desc())
    total = query.count()
    
    users = query.offset(pagination.offset).limit(pagination.page_size).all()
    
    pages = (total + pagination.page_size - 1) // pagination.page_size
    
    paginated = PaginatedResponse[UserResponse](
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages
    )
    
    return SuccessResponse(data=paginated)
