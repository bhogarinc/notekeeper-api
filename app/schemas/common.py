"""Common schemas shared across modules."""
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    items: List[T] = Field(description="List of items for current page")
    total: int = Field(ge=0, description="Total number of items")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(description="Human-readable error message")
    code: str = Field(description="Machine-readable error code")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = Field(default=False)
    error: ErrorDetail = Field(description="Error details")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class ValidationErrorResponse(BaseModel):
    """Validation error response with multiple field errors."""
    success: bool = Field(default=False)
    errors: List[ErrorDetail] = Field(description="List of validation errors")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response format."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    success: bool = Field(default=True)
    data: T = Field(description="Response data")
    message: Optional[str] = Field(None, description="Optional success message")
    meta: Optional[dict] = Field(None, description="Additional metadata")


class HealthStatus(BaseModel):
    """Health check response."""
    status: str = Field(description="Overall health status")
    version: str = Field(description="API version")
    timestamp: str = Field(description="ISO 8601 timestamp")
    checks: dict = Field(default_factory=dict, description="Component health checks")


class ReadyStatus(BaseModel):
    """Readiness check response."""
    ready: bool = Field(description="Whether service is ready to accept traffic")
    dependencies: dict = Field(default_factory=dict, description="Dependency status")
