# app/core/config.py
"""
Application configuration
Load from environment variables with sensible defaults
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "DinChatbot"
    ENVIRONMENT: str = "development"  # Change to production when deploying
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./chatbot.db"  # Default to SQLite
    
    # Google Gemini (GRATIS!) 🎉
    GEMINI_API_KEY: str = ""  # Get from https://makersuite.google.com/app/apikey
    
    # AI Settings
    USE_AI_FALLBACK: bool = True
    MAX_AI_REQUESTS_PER_DAY: int = 1000  # Per client
    
    # Web Scraping
    MAX_PAGES_TO_CRAWL: int = 20
    CRAWL_TIMEOUT_SECONDS: int = 10
    USER_AGENT: str = "DinChatbot-Trainer/2.0"
    
    # GDPR
    DATA_RETENTION_DAYS: int = 90
    LEAD_ENCRYPTION_KEY: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # Webhooks
    WEBHOOK_SECRET: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALLOWED_HOSTS: list = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # Frontend
    WIDGET_URL: str = "http://localhost:8000/widget.js"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Validation
def validate_settings():
    """Validate critical settings"""
    errors = []
    
    # Gemini API key check (optional - can run without AI)
    if not settings.GEMINI_API_KEY:
        print("⚠️  WARNING: GEMINI_API_KEY not set - AI fallback disabled")
        print("   Get a FREE API key: https://makersuite.google.com/app/apikey")
        # Don't fail - just disable AI
        settings.USE_AI_FALLBACK = False
    
    if settings.ENVIRONMENT == "production":
        if settings.SECRET_KEY == "change-this-in-production":
            errors.append("SECRET_KEY must be changed in production")
        
        if settings.DATABASE_URL.startswith("sqlite"):
            print("⚠️  WARNING: SQLite not recommended for production")
            print("   Use PostgreSQL instead")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

# Run validation on import (only if not testing)
if os.getenv("TESTING") != "true":
    validate_settings()
