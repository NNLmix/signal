import os
import sys

# === Binance API ===
# Main REST API endpoint (can be overridden for testnet or alternatives)
BINANCE_BASE = os.getenv("BINANCE_BASE", "https://api.binance.com")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# === Telegram Bot ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# === Supabase ===
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# === Redis ===
REDIS_URL = os.getenv("REDIS_URL", "")

# === AI / Models ===
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FAST_MODEL_PATH = os.getenv("FAST_MODEL_PATH", "/app/models/fast_lgbm.pkl")

# === App / Deployment ===
KOYEB_APP_URL = os.getenv("KOYEB_APP_URL", "http://localhost:8000")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"{KOYEB_APP_URL}/webhook")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def _log_config():
    """Print current config values at startup for debugging."""
    print("\n====== App Configuration ======", file=sys.stderr)
    print(f"BINANCE_BASE   = {BINANCE_BASE}", file=sys.stderr)
    print(f"KOYEB_APP_URL  = {KOYEB_APP_URL}", file=sys.stderr)
    print(f"WEBHOOK_URL    = {WEBHOOK_URL}", file=sys.stderr)
    print(f"LOG_LEVEL      = {LOG_LEVEL}", file=sys.stderr)

    # Sensitive values: only log if present, but mask for safety
    print(f"BINANCE_API_KEY = {'SET' if BINANCE_API_KEY else 'MISSING'}", file=sys.stderr)
    print(f"SUPABASE_URL    = {'SET' if SUPABASE_URL else 'MISSING'}", file=sys.stderr)
    print(f"REDIS_URL       = {'SET' if REDIS_URL else 'MISSING'}", file=sys.stderr)
    print(f"TELEGRAM_BOT    = {'SET' if TELEGRAM_BOT_TOKEN else 'MISSING'}", file=sys.stderr)
    print("================================\n", file=sys.stderr)


# Log configuration once at import
_log_config()
