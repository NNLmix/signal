import os, asyncio, logging
logger = logging.getLogger(__name__)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

try:
    import openai
    openai.api_key = OPENAI_API_KEY
except Exception:
    openai = None

async def _openai_eval(prompt: str, model: str = "gpt-4o-mini") -> dict:
    try:
        if openai is None:
            raise RuntimeError("openai library not available")
        if hasattr(openai.ChatCompletion, "acreate"):
            resp = await openai.ChatCompletion.acreate(
                model=model,
                messages=[{"role":"user", "content": prompt}],
                max_tokens=200
            )
            content = resp.choices[0].message.content
        else:
            def blocking():
                return openai.Completion.create(model=model, prompt=prompt, max_tokens=200)
            resp_blocking = await asyncio.to_thread(blocking)
            content = resp_blocking.choices[0].text
        return {"score": 0.5, "rationale": content}
    except Exception as e:
        logger.exception("ai.openai.error %s", e)
        return {"score": 0.5, "rationale": "error"}
