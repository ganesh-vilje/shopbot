from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    COMPANY_NAME: str = "ShopBot"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://postgres:root@localhost:5432/shopbot_db1"

    # Redis
    REDIS_URL: str = "redis://:redis_secret@redis:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change_this_secret_in_production_min_32_chars_long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OpenAI
    OPENAI_API_KEY: str = ""



    # OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/oauth/callback"
    GITHUB_CLIENT_ID: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/auth/oauth/github/callback"


    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://frontend:3000",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
