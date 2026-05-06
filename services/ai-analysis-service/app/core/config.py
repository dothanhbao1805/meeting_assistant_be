# config.py của ai-analysis-service
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AI_ANALYSIS_DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"
    SERVICE_PORT: int = 8006

    MEETING_SERVICE_URL: str = "http://meeting-service:8005/api/v1"
    TRANSCRIPTION_SERVICE_URL: str = "http://transcription-service:8004/api/v1"
    COMPANY_SERVICE_URL: str = "http://company-service:8003"
    INTERNAL_SERVICE_KEY: str = "super-secret-internal-key-2026"
    AUTH_SERVICE_URL: str = "http://auth-service:8001"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    class Config:
        env_file = ".env"  # dùng khi chạy local
        env_file_encoding = "utf-8"


settings = Settings()
