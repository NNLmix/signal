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


## Runtime behavior
- Scans **every ~1 second** across configured pairs and all strategies.
- Signals include **Entry/SL/TP** (ATR-based; fallback to 0.5%/1%).
- A keepalive task pings `/healthz` every `KEEPALIVE_SEC` (default 60s) to keep the Koyeb instance warm.


### Test strategy
- `btc_price_gt_threshold` (1m): Emits a **LONG** signal when BTCUSDT last close > `TEST_SIGNAL_PRICE` (default **110000.0**).
- Toggle via `TEST_SIGNAL_ENABLED=true/false`. Override price with `TEST_SIGNAL_PRICE`.


## Redis TLS notes
- Use the exact endpoint/port shown in Redis Cloud:
  - **TLS endpoint** → `rediss://` + TLS port
  - **Non-TLS endpoint** → `redis://` + non-TLS port
- If you see `SSL record layer failure`, you are likely using TLS against a non‑TLS port. Fix the URL/port. As a temporary workaround:
  - Set `REDIS_ALLOW_TLS_DOWNGRADE=true` (the client will retry without TLS)
  - Or set `REDIS_SSL_VERIFY=false` if you have a certificate chain issue (not recommended long-term).
