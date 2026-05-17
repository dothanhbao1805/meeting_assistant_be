from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    COMPANY_DATABASE_URL: str
    SMTP_HOST: str = ""
    SMTP_PORT: int = 588
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_SECURE: bool = True
    HF_TOKEN: str
    API_BASE_URL: str = "http://company-service:8003/api/v1"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/google/callback"

    class Config:
        env_file = ".env"


settings = Settings()
