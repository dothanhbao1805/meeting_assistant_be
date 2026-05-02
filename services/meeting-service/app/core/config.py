# meeting-service/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MEETING_DATABASE_URL: str
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_BUCKET: str = "meeting-files"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    REDIS_URL: str = "redis://redis:6379"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()