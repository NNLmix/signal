import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
LOG_LEVEL = os.getenv("LOG_LEVEL","INFO")
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
