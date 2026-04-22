from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AI_ANALYSIS_DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"
    SERVICE_PORT: int = 8006

    class Config:
        env_file = ".env"


settings = Settings()
