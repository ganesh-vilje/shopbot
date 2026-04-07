import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
        enable_decoding=False,
    )

    COMPANY_NAME: str = "ShopBot"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1"

    DATABASE_URL: str = "postgresql://shopbot:shopbot_secret@postgres:5432/shopbot_db"

    JWT_SECRET_KEY: str = "change_me_before_production_use_a_random_32_char_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15 #minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30 #days
    COOKIE_DOMAIN: str = ""
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    OPENAI_API_KEY: str = ""

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://frontend:3000"

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalised = value.lower()
        if normalised not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none")
        return normalised

    @field_validator("DEBUG", "COOKIE_SECURE", mode="before")
    @classmethod
    def parse_bool_like_values(cls, value):
        if isinstance(value, str):
            normalised = value.strip().lower()
            if normalised in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalised in {"0", "false", "no", "off", "release", "production"}:
                return False
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @staticmethod
    def _parse_list_setting(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        if not isinstance(value, str):
            return []

        raw_value = value.strip()
        if not raw_value:
            return []

        if raw_value.startswith("["):
            try:
                decoded = json.loads(raw_value)
            except json.JSONDecodeError:
                decoded = None
            if isinstance(decoded, list):
                return [str(item).strip() for item in decoded if str(item).strip()]

        return [item.strip() for item in raw_value.split(",") if item.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        return self._parse_list_setting(self.TRUSTED_HOSTS)

    @property
    def allowed_origins(self) -> list[str]:
        return self._parse_list_setting(self.ALLOWED_ORIGINS)

    def validate_runtime(self) -> None:
        if self.is_production:
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if self.JWT_SECRET_KEY.startswith("change_me_before_production"):
                raise ValueError("JWT_SECRET_KEY must be changed in production")
            if not self.COOKIE_SECURE:
                raise ValueError("COOKIE_SECURE must be true in production")
            if self.FRONTEND_URL.startswith("http://"):
                raise ValueError("FRONTEND_URL must use https in production")
            if self.BACKEND_URL.startswith("http://"):
                raise ValueError("BACKEND_URL must use https in production")
            localhost_origins = [origin for origin in self.allowed_origins if "localhost" in origin]
            if localhost_origins:
                raise ValueError("ALLOWED_ORIGINS cannot include localhost in production")


@lru_cache()
def get_settings() -> Settings:
    loaded_settings = Settings()
    loaded_settings.validate_runtime()
    return loaded_settings


get_settings.cache_clear()
settings = get_settings()
