"""Environment-driven settings. Nothing in this file should hold a secret's actual
value — only where to read it from.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required secrets
    anthropic_api_key: str
    voyage_api_key: str

    # Database
    database_url: str = "postgresql://precedent:precedent@localhost:5433/precedent"

    # Models
    agent_model: str = "claude-sonnet-5"
    classifier_model: str = "claude-haiku-4-5-20251001"
    embedding_model: str = "voyage-law-2"
    embedding_dim: int = 1024

    # App
    precedent_env: str = "dev"
    log_level: str = "INFO"

    # Pricing, USD per million tokens — kept here (not hardcoded in governance.py) so a
    # pricing change is a one-line edit. Verify against platform.claude.com/docs before
    # trusting these for anything beyond a rough cost estimate.
    pricing_per_mtok: dict[str, tuple[float, float]] = {
        "claude-sonnet-5": (2.0, 10.0),
        "claude-haiku-4-5-20251001": (1.0, 5.0),
        "claude-opus-5": (5.0, 25.0),
    }


settings = Settings()  # type: ignore[call-arg]  # populated from .env at import time
