"""
sentinel/config/settings.py
============================
Central configuration — reads from .env via pydantic-settings.

DESIGN DECISION:
    We use a single settings singleton imported everywhere.
    This means:
    - One place to change model, limits, paths
    - Tests can override settings cleanly
    - No scattered os.environ calls across the codebase

ADDITIVE MODULE:
    New settings are appended as new days need them.
    Existing settings are never removed or renamed.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):

    # ── Claude API ───────────────────────────────────────────────────
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    claude_model: str = Field(
        default="claude-sonnet-4-5",
        env="CLAUDE_MODEL"
    )
    max_tokens: int = Field(default=8096, env="MAX_TOKENS")

    # ── App ──────────────────────────────────────────────────────────
    environment: str = Field(
        default="development",
        env="ENVIRONMENT"
    )
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # ── Business Rules ───────────────────────────────────────────────
    # Day 1: used in customer_tools.py
    # Day 7: enforced programmatically via hooks
    refund_approval_limit: float = Field(
        default=500.00,
        env="REFUND_APPROVAL_LIMIT"
    )

    # ── Data ─────────────────────────────────────────────────────────
    mock_data_path: str = Field(
        default="./data/mock",
        env="MOCK_DATA_PATH"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton — import this everywhere
# Usage: from sentinel.config.settings import settings
settings = Settings()