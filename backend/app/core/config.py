
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    elexon_api_base_url: str = Field(
        default="https://data.elexon.co.uk/bmrs/api/v1",
        description="Base URL for Elexon BMRS Insights API v1"
    )

    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"

    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://windledger-frontend.onrender.com"
    ]

    # Day-Ahead Decision Cutoff Defaults
    # Default 11:00 UTC on D-1 (standard UK day-ahead wholesale market auction cutoff)
    default_cutoff_hour_utc: int = 11
    default_cutoff_day_offset: int = 1

    # Network and resilience
    http_timeout_seconds: float = 15.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.5
    cache_ttl_seconds: int = 3600

    # Fixture fallback mode
    force_fixture_mode: bool = False
    # Fail closed by default: never silently substitute unverified fixtures for live data.
    # Set ALLOW_FIXTURE_FALLBACK=true only when the UI clearly labels fixture data.
    allow_fixture_fallback: bool = False
    fixture_dir: str = str(Path(__file__).resolve().parents[2] / "fixtures")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
