from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Odoo Analytics API", alias="APP_NAME")
    app_env: str = Field(default="production", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    secret_key: str = Field(alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_minutes: int = Field(default=10080, alias="JWT_REFRESH_TOKEN_EXPIRE_MINUTES")
    jwt_issuer: str = Field(default="odoo-analytics-api", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="analytics-clients", alias="JWT_AUDIENCE")
    cors_origins: list[str] = Field(default_factory=list, alias="CORS_ORIGINS")
    trusted_hosts: list[str] = Field(default_factory=list, alias="TRUSTED_HOSTS")
    secure_ssl_redirect: bool = Field(default=False, alias="SECURE_SSL_REDIRECT")
    swagger_enabled: bool = Field(default=True, alias="SWAGGER_ENABLED")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")

    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(alias="DB_NAME")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")
    db_schema: str = Field(default="analytics", alias="DB_SCHEMA")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=40, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    redis_url: str = Field(alias="REDIS_URL")
    redis_default_ttl: int = Field(default=300, alias="REDIS_DEFAULT_TTL")
    rate_limit_default: str = Field(default="120/minute", alias="RATE_LIMIT_DEFAULT")
    rate_limit_auth: str = Field(default="20/minute", alias="RATE_LIMIT_AUTH")

    admin_email: str = Field(alias="ADMIN_EMAIL")
    admin_password: str = Field(alias="ADMIN_PASSWORD")
    admin_full_name: str = Field(default="Platform Admin", alias="ADMIN_FULL_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
