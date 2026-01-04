"""
Application Configuration
Load settings from environment variables (.env file)
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Define all config here so it can be used throughout the app.
    Example: from app.config import settings
    """
    
    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    
    DATABASE_URL: str
    """PostgreSQL connection string"""
    
    DATABASE_POOL_SIZE: int = 10
    """Number of database connections to keep in pool"""
    
    DATABASE_MAX_OVERFLOW: int = 20
    """Additional connections beyond pool_size when needed"""
    
    # ========================================================================
    # AUTHENTICATION CONFIGURATION
    # ========================================================================
    
    SECRET_KEY: str
    """Secret key for signing JWT tokens - MUST be strong random string"""
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    """JWT token expiration time in minutes"""
    
    ALGORITHM: str = "HS256"
    """Algorithm for JWT token signing"""
    
    # ========================================================================
    # CLOUDINARY CONFIGURATION (File Storage)
    # ========================================================================
    
    CLOUDINARY_CLOUD_NAME: str
    """Cloudinary cloud name for file uploads"""
    
    CLOUDINARY_API_KEY: str
    """Cloudinary API key"""
    
    CLOUDINARY_API_SECRET: str
    """Cloudinary API secret"""
    
    # ========================================================================
    # CLAUDE API CONFIGURATION (AI Extraction)
    # ========================================================================
    
    CLAUDE_API_KEY: str
    """Anthropic Claude API key"""
    
    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    """Claude model to use for extractions"""
    
    # ========================================================================
    # APPLICATION CONFIGURATION
    # ========================================================================
    
    ENVIRONMENT: str = "development"
    """Environment: development, staging, or production"""
    
    LOG_LEVEL: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"""
    
    # ========================================================================
    # FRONTEND CONFIGURATION
    # ========================================================================
    
    FRONTEND_URL: str = "http://localhost:5173"
    """Frontend application URL for CORS"""
    
    # ========================================================================
    # PYDANTIC CONFIGURATION
    # ========================================================================
    
    class Config:
        """Load from .env file"""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env variables


# ============================================================================
# INSTANTIATE SETTINGS
# ============================================================================

settings = Settings()

# ============================================================================
# VALIDATION
# ============================================================================

# Validate critical settings on startup
def validate_settings():
    """Validate that all required settings are configured"""
    required_fields = [
        "DATABASE_URL",
        "SECRET_KEY",
        "CLAUDE_API_KEY",
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
    ]
    
    missing = []
    for field in required_fields:
        if not getattr(settings, field):
            missing.append(field)
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please check your .env file."
        )


# Validate on import (will fail fast if .env is missing required vars)
try:
    validate_settings()
except ValueError as e:
    print(f"⚠️  Warning: {str(e)}")