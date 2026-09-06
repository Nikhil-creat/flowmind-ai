"""
Central application configuration.
Values are loaded from environment variables (see .env.example at repo root).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "FlowMind AI"
    ENV: str = "development"

    # Auth
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # Database
    DATABASE_URL: str = "sqlite:///./flowmind.db"

    # AI providers - Claude is primary, Gemini is the automatic fallback if
    # Claude errors out or isn't configured (multi-provider reliability).
    AI_PROVIDER: str = "claude"  # "claude" | "gemini"
    ANTHROPIC_API_KEY: str | None = None
    AI_MODEL: str = "claude-sonnet-4-6"
    GOOGLE_API_KEY: str | None = None       # Gemini - console.cloud.google.com / aistudio.google.com
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Google Sign-In (OAuth) - console.cloud.google.com > APIs & Services > Credentials
    GOOGLE_CLIENT_ID: str | None = None

    # Vector store
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Reliability / performance
    REDIS_URL: str | None = None  # e.g. redis://localhost:6379/0 - enables caching + rate limiting store
    RATE_LIMIT_CHAT: str = "20/minute"
    RATE_LIMIT_WORKFLOW_RUN: str = "30/minute"
    CACHE_TTL_SECONDS: int = 300

    # Billing (optional) - Stripe Checkout for upgrading a workspace to "pro"
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PRICE_ID_PRO: str | None = None
    FRONTEND_URL: str = "http://localhost:3000"

    # Integrations (all optional - workflow nodes log instead of failing if unset)
    SLACK_DEFAULT_WEBHOOK_URL: str | None = None
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_WHATSAPP_FROM: str | None = None  # e.g. "whatsapp:+14155238886"
    GOOGLE_SERVICE_ACCOUNT_JSON: str | None = None  # path to a service-account JSON file

    # Outbound email (used by the workflow "send_email" action node)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
