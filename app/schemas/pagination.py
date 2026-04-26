"""
Pagination schemas for NoteKeeper API.

Provides generic pagination support for list endpoints.
"""

from math import ceil
from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Parameters for paginated queries.
    
    Extracted from query parameters in list endpoints.
    """
    page: int = Field(
        default=1, 
        ge=1,
        description="Page number (1-indexed)"
    )
    limit: int = Field(
        default=20, 
        ge=1, 
        le=100,
        description="Number of items per page (max 100)"
    )
    
    @property
    def skip(self) -> int:
        """
        Calculate SQL OFFSET value.
        
        Returns:
            Number of items to skip for pagination
        """
        return (self.page - 1) * self.limit
    
    @property
    def offset(self) -> int:
        """Alias for skip property."""
        return self.skip


class PaginationState(BaseModel):
    """
    Pagination metadata for responses.
    
    Provides clients with information about available pages.
    """
    page: int = Field(
        ...,
        description="Current page number"
    )
    limit: int = Field(
        ...,
        description="Items per page"
    )
    total: int = Field(
        ...,
        description="Total number of items"
    )
    total_pages: int = Field(
        ...,
        description="Total number of pages"
    )
    has_next: bool = Field(
        ...,
        description="Whether a next page exists"
    )
    has_prev: bool = Field(
        ...,
        description="Whether a previous page exists"
    )
    
    @classmethod
    def create(
        cls,
        page: int,
        limit: int,
        total: int
    ) -> "PaginationState":
        """
        Factory method to create pagination state.
        
        Args:
            page: Current page number
            limit: Items per page
            total: Total number of items
            
        Returns:
            Configured PaginationState instance
        """
        total_pages = ceil(total / limit) if total > 0 else 1
        
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.
    
    Wraps any list of items with pagination metadata.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    items: List[T] = Field(
        ...,
        description="List of items for current page"
    )
    pagination: PaginationState = Field(
        ...,
        description="Pagination metadata"
    )
    
    @classmethod
    def create(
        cls,
        items: List[T],
        params: PaginationParams,
        total: int
    ) -> "PaginatedResponse[T]":
        """
        Factory method to create paginated response.
        
        Args:
            items: List of items for current page
            params: Pagination parameters used
            total: Total number of items
            
        Returns:
            Configured PaginatedResponse instance
        """
        pagination = PaginationState.create(
            params.page,
            params.limit,
            total
        )
        
        return cls(
            items=items,
            pagination=pagination
        )
