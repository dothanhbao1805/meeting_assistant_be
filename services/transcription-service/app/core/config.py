from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TRANSCRIPTION_DATABASE_URL: str
    SERVICE_PORT: int = 8004
    REDIS_URL: str = "redis://redis:6379"

    # Deepgram Config
    DEEPGRAM_API_KEY: str
    DEEPGRAM_API_KEY_ID: Optional[str] = None
    DEEPGRAM_WEBHOOK_BASIC_USERNAME: Optional[str] = None
    DEEPGRAM_WEBHOOK_BASIC_PASSWORD: Optional[str] = None
    DEEPGRAM_WEBHOOK_SECRET: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # Webhook URL (for Deepgram callback)
    WEBHOOK_URL: str = "https://api-gateway:8000/api/v1/webhooks/deepgram"
    COMPANY_SERVICE_URL: str = "http://company-service:8003"

    # Event Publishing
    REDIS_CHANNEL_TRANSCRIPTION: str = "event:transcription"

    COMPANY_SERVICE_URL: str
    MEETING_SERVICE_URL: str
    SPEAKER_SIMILARITY_THRESHOLD: float = 0.75

    HF_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
