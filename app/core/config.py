"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "NoteKeeper API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:pass@localhost/notekeeper"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://notekeeper.bhogar.ai"
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Azure
    AZURE_APP_NAME: str = os.getenv("AZURE_APP_NAME", "notekeeper-bhogarai")
    AZURE_LOCATION: str = os.getenv("AZURE_LOCATION", "centralus")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
