"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Penny Stock Picker"
    debug: bool = False
    secret_key: str = "change-this-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/penny_stocks"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT Authentication
    jwt_secret_key: str = "jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # API Keys - Market Data
    polygon_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    sec_api_key: Optional[str] = None

    # API Keys - News & Social
    benzinga_api_key: Optional[str] = None
    stock_news_api_key: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "PennyStockPicker/1.0"

    # Broker - Alpaca
    alpaca_api_key: Optional[str] = None
    alpaca_api_secret: Optional[str] = None
    alpaca_paper: bool = True  # Use paper trading by default

    # Notifications
    sendgrid_api_key: Optional[str] = None
    from_email: str = "alerts@pennystockpicker.com"
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None

    # Frontend
    frontend_url: str = "https://penny.co-l.in"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://penny.co-l.in",
    ]

    # Penny Stock Criteria
    penny_stock_max_price: float = 5.00
    penny_stock_min_volume: int = 10000


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
