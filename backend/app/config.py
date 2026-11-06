import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "FixLoop API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./fixloop.db"
    
    # Hindsight Memory Config
    HINDSIGHT_BASE_URL: str = "https://api.hindsight.cloud"
    HINDSIGHT_API_KEY: str = ""
    HINDSIGHT_BANK_OR_AGENT_ID: str = "fixloop-operations"
    
    # Groq LLM Config
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
