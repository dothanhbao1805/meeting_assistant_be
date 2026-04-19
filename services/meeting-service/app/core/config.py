from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


SERVICE_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = SERVICE_ROOT / "app"


class Settings(BaseSettings):
    MEETING_DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_BUCKET: str = "meeting-files"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    REDIS_URL: str = "redis://redis:6379"

    model_config = SettingsConfigDict(
        env_file=(SERVICE_ROOT / ".env", APP_DIR / ".env"),
        extra="ignore",
    )


settings = Settings()
