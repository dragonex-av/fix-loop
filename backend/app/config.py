import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "FixLoop API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # Database (Defaults to SQLite for local deterministic benchmark/testing, or NeonDB if DATABASE_URL is set in .env)
    DATABASE_URL: str = "sqlite:///./fixloop.db"
    
    # Auth
    JWT_SECRET: str = "fixloop-super-secure-jwt-secret-key-2026-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    
    # Role allowlists (comma-separated emails)
    ADMIN_EMAILS: str = "admin@fixloop.com,sarah.jenkins@fixloop.com"
    TECHNICIAN_EMAILS: str = "tech.vikram@fixloop.com,tech.rajesh@fixloop.com,deepak.v@fixloop.com,support@fixloop.com"
    
    # Hindsight Memory Config
    HINDSIGHT_BASE_URL: str = "https://api.hindsight.vectorize.io"
    HINDSIGHT_API_KEY: str = ""
    HINDSIGHT_BANK_OR_AGENT_ID: str = "fixloop-operations"
    
    # Groq LLM Config
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    
    # Business Rules & Config
    REPEAT_WINDOW_DAYS: int = 30
    RIPPLE_THRESHOLD: int = 3
    SMTP_ENABLED: bool = False
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
