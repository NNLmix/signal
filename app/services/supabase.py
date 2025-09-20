import aiohttp
from ..config import settings
from typing import Dict, Any

class SupabaseClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def insert_signal(self, row: Dict[str, Any]):
        url = f"{settings.SUPABASE_URL}/rest/v1/signals"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        async with self.session.post(url, headers=headers, json=row, timeout=10) as r:
            if r.status >= 400:
                text = await r.text()
                raise RuntimeError(f"supabase_insert_error status={r.status} body={text}")
