# Signal Router (Futures Scalp 5m + MACD Retest)

- **Signals only**: no live order placement; Binance integration fetches candles for analysis.
- **Redis** for: features cache, queue, dedup, last processed candle timestamp.
- **Supabase** for: persisted signals (`signals` table) and AI evals (`ai_evals` table).

## Strategies
1. `scalp_5m`: EMA20/50 structure + RSI(14) 50-cross, trend filter via EMA200 slope.  
   - TP/SL from environment:
     - `SCALP_SL_ATR` (default 1.0×ATR)
     - `SCALP_TP_ATR` (default 2.0×ATR)  → RR ≈ 1:2
2. `macd_retest_5m`: MACD histogram cross with EMA20 retest; HTF (1h) EMA200 slope bias; RR ≈ 1:1.5.

## Env
```
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
REDIS_URL=redis://:password@host:port/0
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
AI_PROVIDER=supabase   # or 'openai' + OPENAI_API_KEY
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT
LTF=5m
HTF=1h
TRADE_EXECUTION_ENABLED=false   # signals only
SCALP_SL_ATR=1.0
SCALP_TP_ATR=2.0
```

## Supabase schema
```sql
alter table signals add column if not exists dedup_key text;
create unique index if not exists signals_dedup_key_unique on signals(dedup_key);
```


### Model path override
Set `FAST_MODEL_PATH` to point to a LightGBM native `.txt` or pickled Booster `.pkl` (e.g. `/app/models/fast_lgbm.pkl`).
