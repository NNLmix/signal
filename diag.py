import asyncio, aiohttp, time
from typing import Dict, Any
from config import SUPABASE_URL, BINANCE_BASE, SYMBOLS, LTF, HTF
from redis_client import is_available as redis_ok, queue_len
from redis_client import _host_port_tls

async def supabase_ok() -> Dict[str, Any]:
    # Prefer the auth health endpoint (no auth required)
    url = f"{SUPABASE_URL}/auth/v1/health"
    t0 = time.perf_counter()
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=4) as r:
                dt = time.perf_counter() - t0
                return {"ok": r.status == 200, "status": r.status, "latency_ms": round(dt*1000)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

async def binance_ok() -> Dict[str, Any]:
    url = f"{BINANCE_BASE}/fapi/v1/time"
    t0 = time.perf_counter()
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=4) as r:
                dt = time.perf_counter() - t0
                ok = r.status == 200
                data = await r.json(content_type=None) if ok else {"status": r.status}
                return {"ok": ok, "latency_ms": round(dt*1000), "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

async def gather_diag() -> Dict[str, Any]:
    sup_task = asyncio.create_task(supabase_ok())
    bin_task = asyncio.create_task(binance_ok())
    red = {"ok": redis_ok(), "queue_len": queue_len(), "target": _host_port_tls()}
    sup = await sup_task
    bn = await bin_task
    return {
        "redis": red,
        "supabase": sup,
        "binance": bn,
        "symbols": SYMBOLS,
        "ltf": LTF,
        "htf": HTF,
    }