import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Coding Platform"
    
    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db/ai_platform")
    
    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b3c9d1a2f6e5a4b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/1")

settings = Settings()
