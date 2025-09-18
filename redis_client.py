import ssl
import redis.asyncio as redis
from config import REDIS_URL

# SSL-контекст для Koyeb (без проверки сертификата)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Клиент Redis с TLS
redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    ssl=True,
    ssl_cert_reqs=None,
    ssl_context=ssl_context,
)

# ===== Хелперы для diag.py =====
async def is_available() -> bool:
    """Проверка доступности Redis."""
    try:
        pong = await redis_client.ping()
        return pong is True
    except Exception:
        return False

async def queue_len(queue_name: str = "signals") -> int:
    """Длина очереди сигналов."""
    try:
        return await redis_client.llen(queue_name)
    except Exception:
        return -1
