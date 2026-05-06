from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    INTEGRATION_DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"
    SERVICE_PORT: int = 8007
    COMPANY_SERVICE_URL: str = "http://company-service:8003/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
