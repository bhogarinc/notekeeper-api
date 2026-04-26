"""Authentication-related schemas."""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class Token(BaseModel):
    """JWT token response."""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[int] = Field(None, description="User ID from token")
    email: Optional[str] = Field(None, description="User email from token")
    scopes: list = Field(default_factory=list, description="Token scopes")


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, description="User password")


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must include uppercase, lowercase, number)"
    )
    full_name: str = Field(
        min_length=2,
        max_length=100,
        description="User's full name"
    )


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr = Field(description="User email address")


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str = Field(description="Current password")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password"
    )


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str = Field(description="Valid refresh token")
