import json, logging
from typing import Any, Dict
from config import AI_PROVIDER, AI_MODEL, OPENAI_API_KEY
from storage import save_ai_evaluation

logger = logging.getLogger(__name__)

async def _supabase_eval(prompt: str, model: str) -> Dict[str, Any]:
    # Replace with edge function if available
    return {"score": 0.5, "rationale": "neutral-baseline"}

async def _openai_eval(prompt: str, model: str) -> Dict[str, Any]:
    import openai
    openai.api_key = OPENAI_API_KEY
    try:
        comp = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Rate this trading signal from 0 to 1 and explain briefly:\n{prompt}\nReturn JSON with keys score and rationale.",
            max_tokens=120, temperature=0.1,
        )
        text = comp.choices[0].text.strip()
        data = json.loads(text) if text.startswith("{") else {"score": 0.5, "rationale": text}
        return {"score": float(data.get("score", 0.5)), "rationale": data.get("rationale", "")}
    except Exception as e:
        logger.warning("openai_eval.error %s", {"error": str(e)})
        return {"score": 0.5, "rationale": "openai-error"}

def _format_prompt(signal: dict, features: dict) -> str:
    lines = [
        f"Strategy: {signal.get('strategy','unknown')}",
        f"Symbol: {signal.get('symbol')}",
        f"Side: {signal.get('side')}",
        f"Entry: {signal.get('entry_price')}",
        f"TP: {signal.get('tp')}  SL: {signal.get('sl')}",
        f"Reason: {signal.get('reason','')}",
        f"Features: {json.dumps(features, ensure_ascii=False)}",
    ]
    return "\n".join(lines)

async def evaluate_prompt(prompt: str, model: str = AI_MODEL):
    if AI_PROVIDER.lower() == "openai" and OPENAI_API_KEY:
        return await _openai_eval(prompt, model)
    return await _supabase_eval(prompt, model)

async def ask_ai_async(saved_signal: dict, features: dict) -> None:
    try:
        prompt = _format_prompt(saved_signal, features)
        resp = await evaluate_prompt(prompt, model=AI_MODEL)
        score = float(resp.get("score", 0.5))
        rationale = resp.get("rationale", "")
        await save_ai_evaluation(saved_signal.get("id"), score=score, rationale=rationale)
    except Exception as e:
        logger.exception("ai_evaluator.ask_ai_async.error %s", {"error": str(e)})
