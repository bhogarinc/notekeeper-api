"""JWT token handling utilities."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

# Constants
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30


class TokenExpiredError(Exception):
    """Raised when a token has expired."""
    pass


class TokenInvalidError(Exception):
    """Raised when a token is invalid."""
    pass


def create_access_token(
    user_id: str,
    email: str,
    username: str,
    secret_key: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User's UUID
        email: User's email
        username: User's username
        secret_key: Secret key for signing
        expires_delta: Custom expiration time (default: 30 minutes)
        
    Returns:
        Encoded JWT string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "email": email,
        "username": username,
        "type": "access",
        "iat": datetime.utcnow(),
        "exp": expire,
        "jti": str(uuid4())
    }
    
    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, secret_key: str) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        user_id: User's UUID
        secret_key: Secret key for signing
        
    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": datetime.utcnow(),
        "exp": expire,
        "jti": str(uuid4()),
        "token_version": 1
    }
    
    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> Dict[str, Any]:
    """
    Decode and validate an access token.
    
    Args:
        token: JWT access token
        secret_key: Secret key for verification
        
    Returns:
        Decoded token payload
        
    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "access":
            raise TokenInvalidError("Invalid token type")
            
        return payload
        
    except ExpiredSignatureError:
        raise TokenExpiredError("Access token has expired")
    except InvalidTokenError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}")


def decode_refresh_token(token: str, secret_key: str) -> Dict[str, Any]:
    """
    Decode and validate a refresh token.
    
    Args:
        token: JWT refresh token
        secret_key: Secret key for verification
        
    Returns:
        Decoded token payload
        
    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise TokenInvalidError("Invalid token type")
            
        return payload
        
    except ExpiredSignatureError:
        raise TokenExpiredError("Refresh token has expired")
    except InvalidTokenError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}")
