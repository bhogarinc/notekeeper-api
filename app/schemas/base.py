"""Base Pydantic schema classes."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True
    )


class ErrorResponse(BaseSchema):
    """Standard error response schema."""
    
    error: str
    message: str
    details: list = []
    request_id: UUID = None
    timestamp: datetime = None
