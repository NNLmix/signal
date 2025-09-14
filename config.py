import os
from dotenv import load_dotenv

# Load .env locally; on Koyeb you set env vars in the dashboard
load_dotenv()

# --- Supabase ---
# Koyeb name: SUPABASE_URL, SUPABASE_KEY
# Keep the constant names used across the codebase to avoid widespread edits:
SUPABASE_URL = os.getenv("SUPABASE_URL") or ""
# map Koyeb SUPABASE_KEY to the existing constant name SUPABASE_ANON_KEY
SUPABASE_ANON_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""

# --- Redis ---
# Must be a FULL URL with scheme (redis:// or rediss:// or unix://)
# Example: rediss://:password@host:port/0
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --- Telegram ---
# Koyeb name: TELEGRAM_BOT_TOKEN
# Keep the constant name TELEGRAM_TOKEN (used by bot.py/notifier.py)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or ""
# IMPORTANT: Use the exact chat.id integer returned by Telegram (usually NEGATIVE for groups/supergroups).
# e.g. -1004900144984
try:
    TG_GROUP_ID = int((os.getenv("TG_GROUP_ID") or "0").strip())
except ValueError:
    TG_GROUP_ID = 0

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or ""

# --- Logging level ---
LOG_LEVEL = (os.getenv("LOG_LEVEL") or "INFO").upper()
