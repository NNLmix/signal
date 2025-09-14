import os
from typing import Optional, Dict, Any, List
import aiohttp

from config import SUPABASE_URL, SUPABASE_ANON_KEY, LOG_LEVEL
from logging_setup import logger

# Toggle based on env presence
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# ---------------------------
# Mock storage (for local tests / when Supabase is not configured)
# ---------------------------

# A minimal in-memory store so you can test /ai 1 without any DB
# Feel free to extend this as needed.
_MOCK_SIGNALS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "symbol": "BTCUSDT",
        "side": "buy",
        "entry_price": 65000.0,
        "size": 0.01,
        "confidence": 72,  # percent
        "reason": "MA crossover + volume spike",
        "created_at": "2025-09-14T12:00:00Z",
        "status": "new",
        "tg_message_id": None,
    }
}

_MOCK_AI_EVALS: List[Dict[str, Any]] = []


# ---------------------------
# Helpers
# ---------------------------

def _auth_headers_json() -> Dict[str, str]:
    """
    JSON headers with Supabase auth. Used for REST and Edge Functions.
    """
    return {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    }


# ---------------------------
# Public API used by your bot/worker
# ---------------------------

async def get_signal(signal_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a signal by ID.
    - Supabase mode: GET from REST table `signals` (adjust table/columns if different)
    - Mock mode: returns in-memory sample for id=1
    """
    if not USE_SUPABASE:
        return _MOCK_SIGNALS.get(signal_id)

    url = f"{SUPABASE_URL}/rest/v1/signals"
    params = {
        "id": f"eq.{signal_id}",
        "select": "*",
        "limit": 1,
    }
    headers = _auth_headers_json()

    logger.info("get_signal.request %s", {"signal_id": signal_id})
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=params, headers=headers, timeout=30) as r:
            if r.status >= 400:
                body = await r.text()
                logger.error("get_signal.error %s", {"status": r.status, "body": body})
                return None
            data = await r.json()
            return data[0] if data else None


async def save_signal(signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Persist a new signal. Return the saved signal (with id).
    - Supabase mode: insert into `signals` table
    - Mock mode: insert into in-memory store with next id
    """
    if not USE_SUPABASE:
        new_id = max(_MOCK_SIGNALS.keys(), default=0) + 1
        signal = dict(signal)
        signal["id"] = new_id
        _MOCK_SIGNALS[new_id] = signal
        logger.info("save_signal.mock.saved %s", {"id": new_id})
        return signal

    url = f"{SUPABASE_URL}/rest/v1/signals"
    headers = _auth_headers_json()
    # Many Supabase setups require 'Prefer: return=representation' to return the inserted row
    headers["Prefer"] = "return=representation"

    logger.info("save_signal.request %s", {"symbol": signal.get("symbol")})
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=signal, headers=headers, timeout=30) as r:
            if r.status >= 400:
                body = await r.text()
                logger.error("save_signal.error %s", {"status": r.status, "body": body})
                return None
            data = await r.json()
            return data[0] if data else None


async def update_signal_status(signal_id: int, status: str, tg_message_id: Optional[str] = None) -> bool:
    """
    Update signal status (and optional tg_message_id).
    - Supabase mode: PATCH signals set status / tg_message_id
    - Mock mode: update in-memory record
    """
    if not USE_SUPABASE:
        sig = _MOCK_SIGNALS.get(signal_id)
        if not sig:
            return False
        sig["status"] = status
        if tg_message_id is not None:
            sig["tg_message_id"] = tg_message_id
        logger.info("update_signal_status.mock %s", {"id": signal_id, "status": status})
        return True

    url = f"{SUPABASE_URL}/rest/v1/signals"
    params = {"id": f"eq.{signal_id}"}
    payload: Dict[str, Any] = {"status": status}
    if tg_message_id is not None:
        payload["tg_message_id"] = tg_message_id

    headers = _auth_headers_json()
    headers["Prefer"] = "return=minimal"

    logger.info("update_signal_status.request %s", {"id": signal_id, "status": status})
    async with aiohttp.ClientSession() as s:
        async with s.patch(url, params=params, json=payload, headers=headers, timeout=30) as r:
            if r.status >= 400:
                body = await r.text()
                logger.error("update_signal_status.error %s", {"status": r.status, "body": body})
                return False
            return True


async def save_ai_evaluation(
    signal_id: int,
    prompt: str,
    model: str,
    response_text: str,
    verdict: str,
    score: float
) -> bool:
    """
    Persist AI evaluation for a signal.
    - Supabase mode: call your Edge Function `save-ai-eval` OR insert into `ai_evaluations` table.
      (Below uses an Edge Function as per your original code idea.)
    - Mock mode: append to in-memory list
    """
    if not USE_SUPABASE:
        _MOCK_AI_EVALS.append({
            "signal_id": signal_id,
            "request_prompt": prompt,
            "model": model,
            "response_text": response_text,
            "verdict": verdict,
            "score": score,
        })
        logger.info("save_ai_evaluation.mock %s", {"signal_id": signal_id, "score": score})
        return True

    # Edge Function approach (adjust path/name if your function differs)
    url = f"{SUPABASE_URL}/functions/v1/save-ai-eval"
    headers = _auth_headers_json()
    payload = {
        "signal_id": signal_id,
        "request_prompt": prompt,
        "model": model,
        "response_text": response_text,
        "verdict": verdict,
        "score": score,
    }

    logger.info("save_ai_evaluation.request %s", {"signal_id": signal_id})
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers, timeout=30) as r:
            ok = 200 <= r.status < 300
            if not ok:
                body = await r.text()
                logger.error("save_ai_evaluation.error %s", {"status": r.status, "body": body})
                return False
            return True


# Convenience function (optional) to expose mock evaluations for debugging
async def list_mock_ai_evaluations() -> List[Dict[str, Any]]:
    """
    Return in-memory evaluations (mock mode only).
    """
    if USE_SUPABASE:
        return []
    return list(_MOCK_AI_EVALS)
