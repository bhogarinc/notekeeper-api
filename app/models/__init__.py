"""
NoteKeeper - Data Models Package

This package contains all Pydantic models for request/response validation
and data serialization.
"""

from app.models.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInToken,
    LoginRequest,
    TokenPair,
    TokenPayload,
)

from app.models.note import (
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

from app.models.pagination import (
    PaginationParams,
    PaginationState,
    PaginatedResponse,
)

__all__ = [
    # User models
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInToken",
    "LoginRequest",
    "TokenPair",
    "TokenPayload",
    # Note models
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