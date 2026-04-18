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

    class Config:
        env_file = ".env"


settings = Settings()
