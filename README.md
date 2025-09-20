# Binance Futures → Telegram Signals (Koyeb-ready)

Minimal, production-friendly refactor with:
- Single FastAPI app (webhook + health)
- One background worker (fetch → evaluate → dedup → persist → send)
- Async Redis for dedup/cache
- Supabase REST insert (service key)
- aiogram (webhook mode), rate-limited

## Required Koyeb env (Secrets)
- BINANCE_API_KEY
- BINANCE_API_SECRET
- TELEGRAM_BOT_TOKEN
- SUPABASE_SERVICE_KEY
- REDIS_URL

## Required Koyeb env (Config)
- PUBLIC_URL       e.g., https://your-app.koyeb.app
- TELEGRAM_CHAT_ID e.g., -1001234567890
- SUPABASE_URL     e.g., https://xyz.supabase.co

## Optional (defaults)
- BINANCE_BASE=https://fapi.binance.com
- PAIRS=BTCUSDT,ETHUSDT,SOLUSDT
- LTF=5m
- HTF=1h
- LOG_LEVEL=INFO

## Run
docker build -t signals .
docker run -p 8000:8000 --env-file .env signals
