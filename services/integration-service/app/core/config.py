from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    INTEGRATION_DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"
    SERVICE_PORT: int = 8007

    class Config:
        env_file = ".env"


settings = Settings()
