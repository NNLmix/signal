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

# ===== Вспомогательные функции =====
def _host_port_tls():
    """Возвращает хост, порт и TLS-статус из REDIS_URL (для diag.py)."""
    try:
        url = REDIS_URL.replace("rediss://", "")
        host, port = url.split(":")
        return host, int(port), True
    except Exception:
        return "unknown", 0, True

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
