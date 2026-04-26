"""
NoteKeeper - Pydantic Schema Package

This package contains all Pydantic schemas for request/response validation
and data serialization. Schemas are separate from database models to allow
for different representations in API contracts.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInToken,
    LoginRequest,
    TokenPair,
    TokenPayload,
)

from app.schemas.note import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    TagBase,
    TagCreate,
    TagUpdate,
    TagResponse,
    NoteBase,
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteSummary,
    NoteSearchFilters,
)

from app.schemas.pagination import (
    PaginationParams,
    PaginationState,
    PaginatedResponse,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInToken",
    "LoginRequest",
    "TokenPair",
    "TokenPayload",
    # Note schemas
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "TagBase",
    "TagCreate",
    "TagUpdate",
    "TagResponse",
    "NoteBase",
    "NoteCreate",
    "NoteUpdate",
    "NoteResponse",
    "NoteSummary",
    "NoteSearchFilters",
    # Pagination
    "PaginationParams",
    "PaginationState",
    "PaginatedResponse",
]