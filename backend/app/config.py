"""Configuration management for OpenClaw-Harness."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import model_validator, ConfigDict
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_NAME: str = "OpenClaw-Harness"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    JWT_SECRET_KEY: str = "change-me-jwt-secret-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./och.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_ECHO: bool = False

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # --- OpenHarness ---
    OPENHARNESS_CONFIG_DIR: str = str(Path.home() / ".och" / "config")
    OPENHARNESS_DATA_DIR: str = str(Path.home() / ".och" / "data")
    OPENHARNESS_DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
    OPENHARNESS_MAX_TURNS: int = 8
    OPENHARNESS_MAX_TOKENS: int = 4096

    # --- LLM Providers ---
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # --- OpenClaw Integration ---
    OPENCLAW_CONFIG_PATH: str = str(Path.home() / ".openclaw" / "openclaw.json")
    OPENCLAW_SYNC_ENABLED: bool = True
    OPENCLAW_API_KEY_PREFIX: str = "och-"

    # --- Security ---
    ADMIN_PASSWORD: str = ""
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @model_validator(mode="after")
    def _check_default_secrets(self) -> "Settings":
        default_secrets = {
            "SECRET_KEY": "change-me-in-production",
            "JWT_SECRET_KEY": "change-me-jwt-secret-min-32-chars",
        }
        insecure = [name for name, default in default_secrets.items() if getattr(self, name) == default]
        if not insecure:
            return self
        if self.APP_ENV == "development":
            for name in insecure:
                logger.warning("%s 使用了默认值，生产环境中必须更换！", name)
        else:
            raise ValueError(
                f"以下密钥仍为默认值，禁止在非开发环境启动：{', '.join(insecure)}"
            )
        return self

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
