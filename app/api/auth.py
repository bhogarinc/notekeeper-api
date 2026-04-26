"""Authentication API routes."""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token, create_refresh_token,
    verify_password, get_password_hash, verify_token
)
from app.models.user import User
from app.schemas.auth import (
    Token, LoginRequest, RegisterRequest,
    PasswordChangeRequest, PasswordResetRequest, RefreshTokenRequest
)
from app.schemas.common import ErrorResponse, ErrorDetail, SuccessResponse
from app.schemas.user import UserResponse

router = APIRouter()
security = HTTPBearer()


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password.",
    responses={
        201: {"description": "User created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Email already registered"}
    }
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
) -> SuccessResponse[UserResponse]:
    """
    Register a new user account.
    
    - Validates email uniqueness
    - Hashes password securely
    - Returns created user data
    """
    # Check if email exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="EMAIL_EXISTS",
                    message="Email address already registered",
                    field="email"
                )
            ).model_dump()
        )
    
    # Create new user
    hashed_password = get_password_hash(request.password)
    user = User(
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return SuccessResponse(
        data=UserResponse.model_validate(user),
        message="User registered successfully"
    )


@router.post(
    "/login",
    response_model=SuccessResponse[Token],
    summary="User login",
    description="Authenticate user and return JWT tokens.",
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"}
    }
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> SuccessResponse[Token]:
    """
    Authenticate user with email and password.
    
    Returns access and refresh tokens on success.
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INVALID_CREDENTIALS",
                    message="Invalid email or password"
                )
            ).model_dump()
        )
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INVALID_CREDENTIALS",
                    message="Invalid email or password"
                )
            ).model_dump()
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="ACCOUNT_INACTIVE",
                    message="Account is deactivated"
                )
            ).model_dump()
        )
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    token_data = Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return SuccessResponse(
        data=token_data,
        message="Login successful"
    )


@router.post(
    "/refresh",
    response_model=SuccessResponse[Token],
    summary="Refresh access token",
    description="Get new access token using refresh token.",
    responses={
        200: {"description": "Token refreshed"},
        401: {"model": ErrorResponse, "description": "Invalid refresh token"}
    }
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> SuccessResponse[Token]:
    """
    Refresh access token using a valid refresh token.
    """
    try:
        payload = verify_token(request.refresh_token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify user exists and is active
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Generate new tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    token_data = Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return SuccessResponse(
        data=token_data,
        message="Token refreshed successfully"
    )


@router.post(
    "/password/change",
    response_model=SuccessResponse[dict],
    summary="Change password",
    description="Change current user's password.",
    responses={
        200: {"description": "Password changed"},
        400: {"model": ErrorResponse, "description": "Invalid current password"}
    }
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SuccessResponse[dict]:
    """
    Change the current user's password.
    
    Requires current password verification.
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INVALID_PASSWORD",
                    message="Current password is incorrect",
                    field="current_password"
                )
            ).model_dump()
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    return SuccessResponse(
        data={},
        message="Password changed successfully"
    )


@router.post(
    "/password/reset-request",
    response_model=SuccessResponse[dict],
    summary="Request password reset",
    description="Request password reset email (placeholder).",
    responses={
        200: {"description": "Reset email sent if user exists"}
    }
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> SuccessResponse[dict]:
    """
    Request a password reset email.
    
    Always returns success to prevent email enumeration.
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    # In production: send actual email with reset token
    # For now, just acknowledge the request
    
    return SuccessResponse(
        data={},
        message="If the email exists, a password reset link has been sent"
    )
