
import json, time, socket, ssl, os
import redis
from urllib.parse import urlparse
from typing import Optional
from config import REDIS_URL, REDIS_TLS_INSECURE, REDIS_CA_PATH, REDIS_HOST_OVERRIDE

_last_err_log_ts = 0.0
_last_err_msg = ""

def _log_once(msg: str, every_sec: float = 30.0):
    global _last_err_log_ts, _last_err_msg
    now = time.time()
    if now - _last_err_log_ts >= every_sec or msg != _last_err_msg:
        print(msg, flush=True)
        _last_err_log_ts = now
        _last_err_msg = msg

def _ssl_ctx_if_needed(parsed):
    if parsed.scheme == "rediss":
        ctx = ssl.create_default_context(cafile=REDIS_CA_PATH or None)
        if REDIS_TLS_INSECURE:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None

def _apply_host_override(url: str) -> str:
    if not REDIS_HOST_OVERRIDE: return url
    p = urlparse(url)
    # rebuild netloc with override host
    new_netloc = f"{p.username + ':' + p.password + '@' if p.username else ''}{REDIS_HOST_OVERRIDE}:{p.port if p.port else ''}"
    return f"{p.scheme}://{new_netloc}{p.path or ''}"

def _make_client():
    url = _apply_host_override(REDIS_URL)
    parsed = urlparse(url)
    ssl_ctx = _ssl_ctx_if_needed(parsed)
    return redis.Redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=2.0,
        socket_timeout=2.5,
        health_check_interval=30,
        ssl=bool(ssl_ctx),
        ssl_cert_reqs=ssl_ctx.verify_mode if ssl_ctx else None,
        ssl_ca_certs=REDIS_CA_PATH or None,
        ssl_check_hostname=False if REDIS_TLS_INSECURE else True
    )

_redis = _make_client()

FEATURE_HASH_PREFIX = "features:"
SIGNALS_QUEUE = "signals"
DEDUP_SET_PREFIX = "sigdedup:"
CANDLE_CACHE_PREFIX = "candles:"  # per symbol/timeframe cache for last ts

def _host_port_tls():
    try:
        from urllib.parse import urlparse
        u = urlparse(REDIS_URL)
        return {"host": u.hostname, "port": u.port, "scheme": u.scheme, "override": REDIS_HOST_OVERRIDE or None, "tls_insecure": REDIS_TLS_INSECURE}
    except Exception:
        return {}

def is_available() -> bool:
    try:
        info = _host_port_tls()
        host = info.get("override") or info.get("host")
        if host:
            try: socket.gethostbyname(host)
            except Exception as e:
                _log_once(f"redis.dns.error host={host} err={e}")
                return False
        _redis.ping()
        return True
    except Exception as e:
        _log_once(f"redis.ping.error {e}")
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
