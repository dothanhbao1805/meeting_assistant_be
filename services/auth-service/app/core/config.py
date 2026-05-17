from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AUTH_DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    COMPANY_SERVICE_URL: str = "http://company-service:8003"

    class Config:
        env_file = ".env"


settings = Settings()
