"""Categories API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import (
    ErrorResponse, ErrorDetail, SuccessResponse,
    PaginationParams, PaginatedResponse
)

router = APIRouter()


def get_category_or_404(db: Session, category_id: int, user_id: int) -> Category:
    """Get category by ID or raise 404."""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="Category not found"
                )
            ).model_dump()
        )
    return category


@router.get(
    "/",
    response_model=SuccessResponse[PaginatedResponse[CategoryResponse]],
    summary="List categories",
    description="Get all user's categories with note counts."
)
async def list_categories(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[PaginatedResponse[CategoryResponse]]:
    """List all categories for the current user."""
    query = db.query(Category).filter(Category.user_id == current_user.id)
    query = query.order_by(Category.name.asc())
    
    total = query.count()
    categories = query.offset(pagination.offset).limit(pagination.page_size).all()
    
    # Add note counts
    category_items = []
    for cat in categories:
        cat_data = CategoryResponse.model_validate(cat)
        cat_data.notes_count = len(cat.notes)
        category_items.append(cat_data)
    
    pages = (total + pagination.page_size - 1) // pagination.page_size
    
    paginated = PaginatedResponse[CategoryResponse](
        items=category_items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages
    )
    
    return SuccessResponse(data=paginated)


@router.post(
    "/",
    response_model=SuccessResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new category."
)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[CategoryResponse]:
    """
    Create a new category.
    
    Category names must be unique per user.
    """
    # Check for duplicate name
    existing = db.query(Category).filter(
        Category.user_id == current_user.id,
        func.lower(Category.name) == func.lower(category_data.name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="DUPLICATE_NAME",
                    message="Category with this name already exists",
                    field="name"
                )
            ).model_dump()
        )
    
    category = Category(
        name=category_data.name,
        description=category_data.description,
        color=category_data.color,
        icon=category_data.icon,
        user_id=current_user.id
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return SuccessResponse(
        data=CategoryResponse.model_validate(category),
        message="Category created successfully"
    )


@router.get(
    "/{category_id}",
    response_model=SuccessResponse[CategoryResponse],
    summary="Get category",
    description="Get a single category by ID."
)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[CategoryResponse]:
    """Get a specific category with its note count."""
    category = get_category_or_404(db, category_id, current_user.id)
    
    cat_data = CategoryResponse.model_validate(category)
    cat_data.notes_count = len(category.notes)
    
    return SuccessResponse(data=cat_data)


@router.patch(
    "/{category_id}",
    response_model=SuccessResponse[CategoryResponse],
    summary="Update category",
    description="Update an existing category."
)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[CategoryResponse]:
    """Update a category's details."""
    category = get_category_or_404(db, category_id, current_user.id)
    
    update_dict = category_data.model_dump(exclude_unset=True)
    
    # Check for duplicate name if updating name
    if "name" in update_dict:
        existing = db.query(Category).filter(
            Category.user_id == current_user.id,
            func.lower(Category.name) == func.lower(update_dict["name"]),
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="DUPLICATE_NAME",
                        message="Category with this name already exists",
                        field="name"
                    )
                ).model_dump()
            )
    
    for field, value in update_dict.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return SuccessResponse(
        data=CategoryResponse.model_validate(category),
        message="Category updated successfully"
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="Delete a category. Notes will become uncategorized."
)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a category.
    
    Notes in this category will become uncategorized (category_id set to null).
    """
    category = get_category_or_404(db, category_id, current_user.id)
    
    # Notes will have category_id set to null via cascade
    db.delete(category)
    db.commit()
