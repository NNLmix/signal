import json, redis
from config import REDIS_URL

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

FEATURE_HASH_PREFIX = "features:"
SIGNALS_QUEUE = "signals"
DEDUP_SET_PREFIX = "sigdedup:"
CANDLE_CACHE_PREFIX = "candles:"  # per symbol/timeframe cache for last ts

def cache_features(symbol: str, features: dict):
    key = f"{FEATURE_HASH_PREFIX}{symbol}"
    redis_client.hset(key, mapping={k: json.dumps(v, ensure_ascii=False) for k, v in features.items()})

def get_features(symbol: str) -> dict:
    key = f"{FEATURE_HASH_PREFIX}{symbol}"
    raw = redis_client.hgetall(key)
    out = {}
    for k, v in raw.items():
        try: out[k] = json.loads(v)
        except Exception: out[k] = v
    return out

def queue_signal(signal: dict):
    redis_client.lpush(SIGNALS_QUEUE, json.dumps(signal, ensure_ascii=False))

def pop_signal():
    data = redis_client.rpop(SIGNALS_QUEUE)
    return json.loads(data) if data else None

def dedup_try_set(key: str, ttl: int) -> bool:
    ok = redis_client.set(f"{DEDUP_SET_PREFIX}{key}", "1", ex=ttl, nx=True)
    return bool(ok)

def set_last_candle_ts(symbol: str, timeframe: str, ts: int):
    redis_client.set(f"{CANDLE_CACHE_PREFIX}{symbol}:{timeframe}", str(ts))

def get_last_candle_ts(symbol: str, timeframe: str) -> int:
    v = redis_client.get(f"{CANDLE_CACHE_PREFIX}{symbol}:{timeframe}")
    try: return int(v) if v else 0
    except: return 0
