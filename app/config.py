from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # Secrets (configure as Koyeb Secrets)
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    TELEGRAM_BOT_TOKEN: str
    SUPABASE_SERVICE_KEY: str
    REDIS_URL: str

    # Non-secrets
    PUBLIC_URL: str
    TELEGRAM_CHAT_ID: str
    SUPABASE_URL: str

    # Optional tuning
    BINANCE_BASE: str = "https://fapi.binance.com"
    PAIRS: List[str] = ["BTCUSDT","ETHUSDT","SOLUSDT"]
    LTF: str = "5m"
    HTF: str = "1h"
    LOG_LEVEL: str = "INFO"
    REQUEST_TIMEOUT: float = 10.0
    RETRY_MAX: int = 5
    RETRY_BASE_DELAY: float = 0.75
    DEDUP_TTL_SEC: int = 60 * 60 * 24  # 1 day

    model_config = SettingsConfigDict(
        env_file=None,
        env_nested_delimiter="__",
        case_sensitive=False,
    )

settings = Settings()
