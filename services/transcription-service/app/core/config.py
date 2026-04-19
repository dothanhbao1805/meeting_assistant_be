from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TRANSCRIPTION_DATABASE_URL: str
    SERVICE_PORT: int = 8004
    REDIS_URL: str = "redis://redis:6379"

    class Config:
        env_file = ".env"


settings = Settings()
