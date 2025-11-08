from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # App Configuration
    APP_NAME: str = "AI LifeOS - FlowMind"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://flowmind_user:flowmind_password@localhost:5432/flowmind_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    GROK_API_KEY: Optional[str] = None
    GROK_API_URL: str = "https://api.x.ai/v1"
    AI_MODEL: str = "grok-beta"
    AI_MAX_TOKENS: int = 4000
    AI_TEMPERATURE: float = 0.7
    
    # External Services
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    ZOOM_API_KEY: Optional[str] = None
    ZOOM_API_SECRET: Optional[str] = None
    
    # Notification Services
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx"]
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TIMEZONE: str = "UTC"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # WebSocket
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    # Meeting Configuration
    DEFAULT_MEETING_DURATION: int = 30  # minutes
    MEETING_BUFFER_TIME: int = 5  # minutes
    
    # Task Configuration
    DEFAULT_TASK_PRIORITY: str = "medium"
    AUTO_ARCHIVE_COMPLETED_TASKS_DAYS: int = 30
    
    # Productivity Analytics
    PRODUCTIVITY_ANALYSIS_WINDOW_DAYS: int = 30
    FOCUS_SESSION_MIN_DURATION: int = 25  # minutes (Pomodoro)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate critical settings
if not settings.SECRET_KEY or settings.SECRET_KEY == "your-super-secret-key-change-in-production":
    if settings.ENVIRONMENT == "production":
        raise ValueError("SECRET_KEY must be set in production")

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)
