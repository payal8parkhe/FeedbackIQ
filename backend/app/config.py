from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key"

    # LLM Provider: "fake", "openai", "anthropic", "ollama"
    LLM_PROVIDER: str = "fake"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Model designations
    ENRICH_MODEL: str = "gpt-4o-mini"
    ANSWER_MODEL: str = "gpt-4o"
    JUDGE_MODEL: str = "gpt-4o"
    EMBED_MODEL: str = "text-embedding-3-small"

    # Batching & Caching limits
    BATCH_MAX_ITEMS: int = 15
    BATCH_MAX_TOKENS: int = 6000
    MAX_REVIEW_CHARS: int = 2000
    CACHE_TTL_DAYS: int = 30
    ENABLE_REDIS_CACHE: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # Database URL
    DATABASE_URL: str = "sqlite+aiosqlite:///./feedbackiq.db"

    # Retrieval & Q&A
    RRF_K: int = 60
    RETRIEVE_K: int = 30
    CONTEXT_K: int = 8
    MIN_CONFIDENCE: float = 0.5
    DAILY_BUDGET_USD: float = 50.0

    # Prompts & Taxonomy Versions
    PROMPT_VERSION: str = "v1"
    TAXONOMY_VERSION: str = "v1"


settings = Settings()
