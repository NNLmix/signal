import os

ENV = os.getenv("ENV", "prod")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SIGNALS_TABLE = os.getenv("SUPABASE_SIGNALS_TABLE", "signals")
SUPABASE_EVALS_TABLE = os.getenv("SUPABASE_EVALS_TABLE", "ai_evals")
SUPABASE_TIMEOUT = float(os.getenv("SUPABASE_TIMEOUT", "10.0"))

# AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "supabase")  # "supabase" | "openai"
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

# Runtime
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))

# Signals / Strategy
DEDUP_TTL_SEC = int(os.getenv("DEDUP_TTL_SEC", str(3*24*3600)))  # 3 days
SYMBOLS = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT").split(",")
LTF = os.getenv("LTF", "5m")
HTF = os.getenv("HTF", "1h")
BINANCE_BASE = os.getenv("BINANCE_BASE", "https://fapi.binance.com")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "8.0"))
RETRY_MAX = int(os.getenv("RETRY_MAX", "5"))

# Execution (disabled by default; signals only)
TRADE_EXECUTION_ENABLED = os.getenv("TRADE_EXECUTION_ENABLED", "false").lower() in ("1", "true", "yes")

# Scalp risk params (ATR multiples)
SCALP_SL_ATR = float(os.getenv("SCALP_SL_ATR", "1.0"))   # default tighter SL
SCALP_TP_ATR = float(os.getenv("SCALP_TP_ATR", "2.0"))   # default RR ~ 1:2


# External keys (for future use; signals-only now)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# Optional custom path for the LightGBM model (txt or pkl)
FAST_MODEL_PATH = os.getenv("FAST_MODEL_PATH", str((__file__ and __import__('pathlib').Path(__file__).parent / "models" / "fast_lgbm.txt")))


# Redis TLS/DNS options
REDIS_TLS_INSECURE = os.getenv("REDIS_TLS_INSECURE", "false").lower() in ("1","true","yes")
REDIS_CA_PATH = os.getenv("REDIS_CA_PATH", "")  # e.g. /etc/ssl/certs/ca-certificates.crt
REDIS_HOST_OVERRIDE = os.getenv("REDIS_HOST_OVERRIDE", "")  # optional: force a host/IP instead of DNS in REDIS_URL
