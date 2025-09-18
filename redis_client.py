import ssl
import redis.asyncio as redis
from config import REDIS_URL

# SSL-контекст для rediss:// (без проверки сертификатов)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    ssl=True,
    ssl_cert_reqs=None,
    ssl_context=ssl_context,
)
