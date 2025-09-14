import aiohttp
from config import SUPABASE_URL, SUPABASE_ANON_KEY
from logging_setup import logger
async def evaluate_prompt(prompt: str, model: str = "gpt-4o-mini") -> dict:
    url = f"{SUPABASE_URL}/functions/v1/ai-evaluator"
    headers = {"Authorization": f"Bearer {SUPABASE_ANON_KEY}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "model": model}
    logger.info("ai_evaluator.request %s", {"model": model})
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers) as r:
            text = await r.text()
            if r.status >= 400:
                logger.error("ai_evaluator.error %s", {"status": r.status, "body": text})
                raise RuntimeError(f"ai-evaluator failed: {r.status} {text}")
            logger.info("ai_evaluator.ok %s", {"status": r.status})
            return await r.json()
