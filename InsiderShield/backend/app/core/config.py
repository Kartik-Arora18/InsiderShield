from functools import lru_cache
from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsiderShield"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://insidershield_app:change_this_local_dev_password@localhost:5432/insidershield"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: SecretStr = SecretStr("CHANGE_ME_USE_A_RANDOM_SECRET_OF_AT_LEAST_32_CHARACTERS")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_security_settings(self):
        secret = self.jwt_secret_key.get_secret_value()
        if self.app_env.lower() == "production":
            if secret.startswith("CHANGE_ME") or len(secret) < 32:
                raise ValueError("Set JWT_SECRET_KEY to a random secret of at least 32 characters in production")
        if self.access_token_expire_minutes < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
