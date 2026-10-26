"""Environment-driven settings. Nothing in this file should hold a secret's actual
value — only where to read it from.
"""
from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load project .env with override so local precedent settings take precedence over global env vars
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Secrets
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    grok_api_key: str = ""
    grok_base_url: str = "https://api.x.ai/v1"
    grok_model: str = "grok-beta"

    # Database
    database_url: str = "postgresql://precedent:precedent@localhost:5434/precedent"

    # Models
    agent_model: str = "claude-sonnet-5"
    classifier_model: str = "claude-haiku-4-5-20251001"
    embedding_model: str = "voyage-law-2"
    embedding_dim: int = 1024
    rerank_candidates: int = 20  # Number of candidates to fetch for reranking (0 to disable)

    # Local-first mode (SQLite + local embeddings)
    local_mode: bool = False
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    local_db_path: str = "~/.precedent/local.db"
    watch_folders: list[str] = []
    allowed_ingest_roots: list[str] = []

    # App
    precedent_env: str = "dev"
    log_level: str = "INFO"
    rate_limit_requests_per_minute: int = 60  # Default rate limit for API endpoints

    # Authentication settings
    jwt_secret_key: str = ""  # Secret key for JWT signing/validation
    jwt_algorithm: str = "HS256"  # Algorithm for JWT (e.g., HS256, RS256)
    jwt_issuer: str = ""  # Expected issuer in tokens
    jwt_audience: str = ""  # Expected audience in tokens
    jwt_resource_identifier: str = "precedent"  # Resource identifier for role extraction (Keycloak format)
    default_role: str = "public"  # Default role if no roles found in token
    role_to_access_groups: dict[str, list[str]] = {}  # Mapping of roles to access groups
    always_include_public: bool = True  # Always include 'public' access group for demo compatibility

    # Pricing, USD per million tokens — kept here (not hardcoded in governance.py) so a
    # pricing change is a one-line edit. Verify against platform.claude.com/docs before
    # trusting these for anything beyond a rough cost estimate.
    pricing_per_mtok: dict[str, tuple[float, float]] = {
        "claude-sonnet-5": (2.0, 10.0),
        "claude-haiku-4-5-20251001": (1.0, 5.0),
        "claude-opus-5": (5.0, 25.0),
    }


settings = Settings()  # type: ignore[call-arg]  # populated from .env at import time
