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

# Binance public API base
BINANCE_BASE = os.getenv("BINANCE_BASE", "https://fapi.binance.com")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "10"))
RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))

# Webhook (if used)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
