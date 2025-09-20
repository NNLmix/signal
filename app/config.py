from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    # Secrets (Koyeb Secrets)
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    TELEGRAM_BOT_TOKEN: str
    SUPABASE_SERVICE_KEY: str
    REDIS_URL: str

    # Required non-secrets
    SUPABASE_URL: str
    TELEGRAM_CHAT_ID: str

    # Optional public URL (fallback to KOYEB_APP_URL)
    PUBLIC_URL: Optional[str] = None
    KOYEB_APP_URL: Optional[str] = None

    # Tunables / defaults
    BINANCE_BASE: str = "https://fapi.binance.com"
    PAIRS: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    LTF: str = "5m"
    HTF: str = "1h"
    LOG_LEVEL: str = "INFO"
    REQUEST_TIMEOUT: float = 10.0
    RETRY_MAX: int = 5
    RETRY_BASE_DELAY: float = 0.75
    DEDUP_TTL_SEC: int = 60 * 60 * 24  # 1 day
    ATR_SL_MULT: float = 1.0
    ATR_TP_MULT: float = 2.0
    KEEPALIVE_SEC: int = 60

    # Redis TLS controls
    REDIS_SSL_VERIFY: bool = True
    REDIS_ALLOW_TLS_DOWNGRADE: bool = False

    # Test-strategy controls
    TEST_SIGNAL_ENABLED: bool = True
    TEST_SIGNAL_PRICE: float = 110000.0
    TEST_SIGNAL_ONCE: bool = True

    model_config = SettingsConfigDict(
        env_file=None,
        env_nested_delimiter="__",
        case_sensitive=False,
    )

settings = Settings()
