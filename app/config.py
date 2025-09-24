from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict

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

    # Polling cadence
    POLL_INTERVAL_SEC: float = 5.0

    # Keepalive ping
    KEEPALIVE_SEC: int = 60

    # ATR risk params (fallback when a strategy doesn't provide SL/TP)
    ATR_SL_MULT: float = 1.0
    ATR_TP_MULT: float = 2.0

    # Dedup TTL (seconds)
    DEDUP_TTL_SEC: int = 3600

    # Redis TLS knobs
    REDIS_SSL_VERIFY: bool = True
    REDIS_ALLOW_TLS_DOWNGRADE: bool = False

    # Strategy toggles (enable/disable per strategy by name)
    # Names must match Strategy.name values
    STRATEGY_TOGGLES: Dict[str, bool] = {
        "btc_price_gt_threshold": True,
        "trend_pullback_5m": True,
        "four_hour_reentry_5m": True,
    }

    # Default pairs universe
    PAIRS: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

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
