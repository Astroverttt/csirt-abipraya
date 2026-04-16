"""
Application settings loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "production"
    APP_DEBUG: bool = False

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = secrets.token_urlsafe(48)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours

    # ── Wazuh API ─────────────────────────────────────────────────────────────
    WAZUH_API_URL: str = "https://10.10.56.199:55000"
    WAZUH_VERIFY_SSL: bool = False
    WAZUH_API_USERNAME: str = ""
    WAZUH_API_PASSWORD: str = ""

    # ── Wazuh Indexer ─────────────────────────────────────────────────────────
    INDEXER_URL: str = "https://10.10.56.199:9200"
    INDEXER_VERIFY_SSL: bool = False
    INDEXER_USERNAME: str = ""
    INDEXER_PASSWORD: str = ""

    # ── NVD ───────────────────────────────────────────────────────────────────
    NVD_API_KEY: str = ""

    # ── Data ──────────────────────────────────────────────────────────────────
    DATA_DIR: str = "./data"
    DATABASE_URL: str = "postgresql://postgres:postgres@10.10.56.96:5432/patchops"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def data_path(self) -> Path:
        p = Path(self.DATA_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
