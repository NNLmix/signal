import logging
import aiohttp
from ..config import settings
log = logging.getLogger('supabase')
from typing import Dict, Any

class SupabaseClient:
    def __init__(self, session: aiohttp.ClientSession):
        log.info('supabase_init', extra={'url': settings.SUPABASE_URL})
        self.session = session

    async def insert_signal(self, row: Dict[str, Any]):
        url = f"{settings.SUPABASE_URL}/rest/v1/signals"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        log.debug('supabase_insert_request', extra={'url': url, 'bytes': len(str(row))})
        async with self.session.post(url, headers=headers, json=row, timeout=10) as r:
            log.info('supabase_insert_response', extra={'status': r.status})
            if r.status >= 400:
                text = await r.text()
                log.error('supabase_insert_error', extra={'status': r.status, 'body': text[:500]}); raise RuntimeError(f"supabase_insert_error status={r.status}")
