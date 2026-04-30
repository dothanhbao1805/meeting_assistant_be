from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AI_ANALYSIS_DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"
    SERVICE_PORT: int = 8006
    
    MEETING_SERVICE_URL: str = "http://meeting-service:8005/api/v1"
    TRANSCRIPTION_SERVICE_URL: str = "http://transcription-service:8004/api/v1"
    
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
