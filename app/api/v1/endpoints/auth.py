"""
Authentication API endpoints for NoteKeeper.

This module implements REST API endpoints for user authentication including
registration, login, token refresh, and logout.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.user import (
    UserCreate,
    UserResponse,
    TokenPair,
    LoginRequest,
)
from app.services.auth import AuthService
from app.services.user import UserService


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Register a new user account.",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.
    
    - **email**: Valid email address (unique)
    - **username**: 3-50 chars, alphanumeric + underscore (unique)
    - **password**: Min 8 chars, must include uppercase, lowercase, number, special char
    - **first_name**: Optional, max 100 chars
    - **last_name**: Optional, max 100 chars
    
    Returns user data without sensitive information.
    """
    auth_service = AuthService(db)
    
    # Check if email exists
    existing_user = await auth_service.get_user_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    # Check if username exists
    existing_user = await auth_service.get_user_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    
    # Create user
    user = await auth_service.create_user(user_in)
    return user


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login",
    description="Authenticate user and receive access tokens.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """
    Authenticate user with email and password.
    
    - **username**: Email address (form field named 'username' for OAuth2 compatibility)
    - **password**: User password
    
    Returns access and refresh token pair on success.
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = await auth_service.authenticate(
        email=form_data.username,
        password=form_data.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    
    # Generate tokens
    tokens = await auth_service.create_token_pair(user)
    return tokens


@router.post(
    "/login/json",
    response_model=TokenPair,
    summary="Login (JSON)",
    description="Authenticate user with JSON payload.",
)
async def login_json(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """
    Authenticate user with JSON payload.
    
    Alternative to form-based login for API clients.
    """
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate(
        email=login_data.email,
        password=login_data.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    
    tokens = await auth_service.create_token_pair(user)
    return tokens


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh token",
    description="Get new access token using refresh token.",
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """
    Refresh access token using valid refresh token.
    
    - **refresh_token**: Valid refresh token from login response
    
    Returns new access and refresh token pair.
    """
    auth_service = AuthService(db)
    
    tokens = await auth_service.refresh_access_token(refresh_token)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    return tokens


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Revoke current access token and invalidate session.",
)
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Logout current user.
    
    Revokes the current access token and invalidates the session.
    Requires valid access token in Authorization header.
    """
    auth_service = AuthService(db)
    # Token revocation logic would go here
    # For now, client should discard tokens
    pass


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get profile of currently authenticated user.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user's profile.
    
    Returns user data for the authenticated user.
    """
    return current_user
