"""Security utilities for password hashing and verification."""
from passlib.context import CryptContext

# Configure bcrypt with work factor of 12
# Higher = more secure but slower
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Work factor
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hashed password string
        
    Example:
        >>> hash_password("SecurePass123!")
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1S'
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Password to verify
        hashed_password: Stored bcrypt hash
        
    Returns:
        True if password matches, False otherwise
        
    Note:
        Uses constant-time comparison to prevent timing attacks
    """
    return pwd_context.verify(plain_password, hashed_password)
