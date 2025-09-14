import redis
from config import REDIS_URL

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def push_price(symbol: str, price: float, volume: float):
    key = f"prices:{symbol}"
    redis_client.lpush(key, f"{price}:{volume}")
    redis_client.ltrim(key, 0, 59)  # только 60 последних точек

def get_prices(symbol: str):
    key = f"prices:{symbol}"
    data = redis_client.lrange(key, 0, -1)
    return [(float(p.split(":")[0]), float(p.split(":")[1])) for p in data]

def cache_features(symbol: str, features: dict):
    key = f"features:{symbol}"
    redis_client.hmset(key, features)

def get_features(symbol: str):
    key = f"features:{symbol}"
    return redis_client.hgetall(key)

def queue_signal(signal: dict):
    redis_client.lpush("signals", str(signal))

def pop_signal():
    data = redis_client.rpop("signals")
    return eval(data) if data else None
