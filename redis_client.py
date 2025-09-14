import json, time, socket
import redis
from typing import Optional
from config import REDIS_URL

# Create client with short connect timeouts; we'll handle failures gracefully.
def _make_client():
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2.0,
        socket_timeout=2.5,
        health_check_interval=30,
    )

_redis = _make_client()

FEATURE_HASH_PREFIX = "features:"
SIGNALS_QUEUE = "signals"
DEDUP_SET_PREFIX = "sigdedup:"
CANDLE_CACHE_PREFIX = "candles:"  # per symbol/timeframe cache for last ts

_last_err_log_ts = 0.0
def _log_once(logger_msg: str, every_sec: float = 30.0):
    global _last_err_log_ts
    now = time.time()
    if now - _last_err_log_ts >= every_sec:
        print(logger_msg, flush=True)
        _last_err_log_ts = now

def is_available() -> bool:
    try:
        # quick resolve + ping
        host = _redis.connection_pool.connection_kwargs.get("host")
        if host:
            try: socket.gethostbyname(host)
            except Exception: return False
        _redis.ping()
        return True
    except Exception:
        return False

def cache_features(symbol: str, features: dict):
    try:
        key = f"{FEATURE_HASH_PREFIX}{symbol}"
        _redis.hset(key, mapping={k: json.dumps(v, ensure_ascii=False) for k, v in features.items()})
    except Exception as e:
        _log_once(f"redis.cache_features.error {e}")

def get_features(symbol: str) -> dict:
    try:
        key = f"{FEATURE_HASH_PREFIX}{symbol}"
        raw = _redis.hgetall(key)
        out = {}
        for k, v in raw.items():
            try: out[k] = json.loads(v)
            except Exception: out[k] = v
        return out
    except Exception as e:
        _log_once(f"redis.get_features.error {e}")
        return {}

def queue_signal(signal: dict):
    try:
        _redis.lpush(SIGNALS_QUEUE, json.dumps(signal, ensure_ascii=False))
    except Exception as e:
        _log_once(f"redis.queue_signal.error {e}")

def pop_signal():
    try:
        data = _redis.rpop(SIGNALS_QUEUE)
        return json.loads(data) if data else None
    except Exception as e:
        _log_once(f"redis.pop_signal.error {e}")
        return None

def dedup_try_set(key: str, ttl: int) -> bool:
    try:
        ok = _redis.set(f"{DEDUP_SET_PREFIX}{key}", "1", ex=ttl, nx=True)
        return bool(ok)
    except Exception as e:
        _log_once(f"redis.dedup_try_set.error {e}")
        # If Redis is down, return False so we don't spam duplicates.
        return False

def set_last_candle_ts(symbol: str, timeframe: str, ts: int):
    try:
        _redis.set(f"{CANDLE_CACHE_PREFIX}{symbol}:{timeframe}", str(ts))
    except Exception as e:
        _log_once(f"redis.set_last_candle_ts.error {e}")

def get_last_candle_ts(symbol: str, timeframe: str) -> int:
    try:
        v = _redis.get(f"{CANDLE_CACHE_PREFIX}{symbol}:{timeframe}")
        try: return int(v) if v else 0
        except: return 0
    except Exception as e:
        _log_once(f"redis.get_last_candle_ts.error {e}")
        return 0


def queue_len() -> int:
    try:
        return int(_redis.llen(SIGNALS_QUEUE))
    except Exception as e:
        _log_once(f"redis.queue_len.error {e}")
        return 0
