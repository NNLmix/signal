import aiohttp
from typing import Optional, Dict, Any
from config import SUPABASE_URL, SUPABASE_ANON_KEY
from logging_setup import logger

async def save_ai_evaluation(signal_id: int, prompt: str, model: str, response_text: str, verdict: str, score: float):
    url = f"{SUPABASE_URL}/functions/v1/save-ai-eval"
    headers = {"Authorization": f"Bearer {SUPABASE_ANON_KEY}", "Content-Type": "application/json"}
    payload = {"signal_id": signal_id, "request_prompt": prompt, "model": model, "response_text": response_text, "verdict": verdict, "score": score}
    logger.info("save_ai_evaluation.request %s", {"signal_id": signal_id})
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers) as r:
            data = await r.json()
            if r.status >= 400:
                logger.error("save_ai_evaluation.error %s", {"status": r.status, "data": data})
                return None
            logger.info("save_ai_evaluation.ok %s", {"status": r.status})
            return data.get("data")

async def save_signal(symbol: str, ts_iso: str, direction: str, entry: float, sl: float, tp: float, size: float, meta: dict):
    url = f"{SUPABASE_URL}/functions/v1/save-signal"
    headers = {"Authorization": f"Bearer {SUPABASE_ANON_KEY}", "Content-Type": "application/json"}
    payload = {"symbol": symbol, "time": ts_iso, "direction": direction, "entry": entry, "sl": sl, "tp": tp, "size": size, "meta": meta or {}}
    logger.info("save_signal.request %s", {"symbol": symbol, "time": ts_iso, "direction": direction})
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers) as r:
            data = await r.json()
            if r.status >= 400:
                logger.error("save_signal.error %s", {"status": r.status, "data": data})
                return None
            logger.info("save_signal.ok %s", {"status": r.status})
            return data.get("data")
