import os
from dotenv import load_dotenv

# Load .env locally; on Koyeb you set env vars in the dashboard
load_dotenv()

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL") or ""
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or ""

# --- Redis ---
# Example: redis://:password@host:port/0
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --- Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or ""
# IMPORTANT: Use the exact chat.id integer returned by Telegram (usually NEGATIVE for groups/supergroups).
# e.g. -1004900144984
TG_GROUP_ID = int(os.getenv("TG_GROUP_ID", "0"))

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or ""

# --- Logging level ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
