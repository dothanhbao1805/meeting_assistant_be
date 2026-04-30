# config.py của ai-analysis-service
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AI_ANALYSIS_DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"
    SERVICE_PORT: int = 8006

    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    TRANSCRIPTION_SERVICE_URL: str = "http://transcription-service:8004"

    class Config:
        env_file = ".env"  # dùng khi chạy local
        env_file_encoding = "utf-8"


settings = Settings()
