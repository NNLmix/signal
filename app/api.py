from fastapi import FastAPI, Request, HTTPException
from aiogram import types
from .telegram import dp, bot
from .config import settings
import asyncio

app = FastAPI()

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/readyz")
async def readyz():
    me = await bot.get_me()
    return {"ok": True, "bot": me.username}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    update = types.Update(**data)
    await dp.process_update(update)
    return {"ok": True}
