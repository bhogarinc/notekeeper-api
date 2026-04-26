"""Cursor-based pagination utilities."""
import base64
import json
from datetime import datetime
from typing import Optional, List, TypeVar, Generic, Any
from pydantic import BaseModel

T = TypeVar('T')


class CursorPaginationParams(BaseModel):
    """Parameters for cursor-based pagination."""
    cursor: Optional[str] = None
    limit: int = 20
    
    class Config:
        json_schema_extra = {
            "example": {
                "cursor": "eyJpZCI6ImFiYzEyMyIsInVwZGF0ZWRfYXQiOiIyMDI2LTA0LTI2VDEwOjMwOjAwWiJ9",
                "limit": 20
            }
        }


class CursorInfo(BaseModel):
    """Cursor information for pagination."""
    next_cursor: Optional[str] = None
    has_more: bool = False
    limit: int = 20
    total_count: Optional[int] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    data: List[T]
    pagination: CursorInfo
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [],
                "pagination": {
                    "next_cursor": "...",
                    "has_more": True,
                    "limit": 20,
                    "total_count": 150
                }
            }
        }


def encode_cursor(cursor_data: dict) -> str:
    """
    Encode cursor data to base64 string.
    
    Args:
        cursor_data: Dictionary with cursor fields
        
    Returns:
        Base64 encoded cursor string
    """
    json_str = json.dumps(cursor_data, default=str)
    return base64.urlsafe_b64encode(json_str.encode()).decode().rstrip('=')


def decode_cursor(cursor: str) -> dict:
    """
    Decode base64 cursor string.
    
    Args:
        cursor: Base64 encoded cursor
        
    Returns:
        Decoded cursor dictionary
        
    Raises:
        ValueError: If cursor is invalid
    """
    try:
        # Add padding if needed
        padding = 4 - len(cursor) % 4
        if padding != 4:
            cursor += '=' * padding
        
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid cursor: {str(e)}")


class CursorPaginator:
    """
    Cursor-based pagination implementation.
    
    Benefits over offset pagination:
    1. Consistent performance regardless of page number
    2. No skipping/duplication when data changes during pagination
    3. Works well with large datasets
    
    Cursor Fields:
    - id: Unique identifier (tie-breaker)
    - updated_at: Sort field for consistent ordering
    """
    
    def __init__(
        self,
        cursor_field: str = "updated_at",
        id_field: str = "id",
        default_limit: int = 20,
        max_limit: int = 100
    ):
        self.cursor_field = cursor_field
        self.id_field = id_field
        self.default_limit = default_limit
        self.max_limit = max_limit
    
    def get_limit(self, requested: Optional[int]) -> int:
        """Get validated limit value."""
        if requested is None:
            return self.default_limit
        return min(max(requested, 1), self.max_limit)
    
    def decode_cursor_values(self, cursor: Optional[str]) -> Optional[dict]:
        """Decode cursor and extract field values."""
        if not cursor:
            return None
        
        try:
            return decode_cursor(cursor)
        except ValueError:
            return None
    
    def encode_next_cursor(self, last_item: Any) -> Optional[str]:
        """Encode cursor for the next page."""
        if not last_item:
            return None
        
        cursor_data = {
            self.cursor_field: getattr(last_item, self.cursor_field),
            self.id_field: str(getattr(last_item, self.id_field))
        }
        return encode_cursor(cursor_data)
