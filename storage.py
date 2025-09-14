import json, logging, aiohttp
from typing import Any, Dict
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SIGNALS_TABLE, SUPABASE_EVALS_TABLE, SUPABASE_TIMEOUT

logger = logging.getLogger(__name__)

_headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

async def _post_json(session, url: str, payload: dict):
    async with session.post(url, data=json.dumps(payload)) as resp:
        text = await resp.text()
        if resp.status >= 300:
            logger.warning("supabase.post.error %s", {"status": resp.status, "body": text})
            raise RuntimeError(f"Supabase error {resp.status}: {text}")
        try:
            return json.loads(text) if text else {}
        except Exception:
            return {"raw": text}

async def save_signal(signal: Dict[str, Any]):
    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_SIGNALS_TABLE}"
    async with aiohttp.ClientSession(headers=_headers, timeout=aiohttp.ClientTimeout(total=SUPABASE_TIMEOUT)) as session:
        payload = [signal]
        return await _post_json(session, url, payload)

async def save_ai_evaluation(signal_id: Any, score: float, rationale: str):
    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_EVALS_TABLE}"
    async with aiohttp.ClientSession(headers=_headers, timeout=aiohttp.ClientTimeout(total=SUPABASE_TIMEOUT)) as session:
        payload = [{"signal_id": signal_id, "score": score, "rationale": rationale}]
        return await _post_json(session, url, payload)
