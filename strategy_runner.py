import hashlib, logging
from typing import List
from config import DEDUP_TTL_SEC
from fast_model import fast_score
from redis_client import cache_features, queue_signal, dedup_try_set
from router import STRATEGIES

logger = logging.getLogger(__name__)

def _dedup_key(sig: dict) -> str:
    base = f"{sig.get('symbol')}|{sig.get('timeframe','')}|{sig.get('strategy')}|{sig.get('candle_open','')}|{sig.get('side')}|{sig.get('entry_price')}|{sig.get('tp')}|{sig.get('sl')}"
    import hashlib as _h; return _h.sha1(base.encode('utf-8')).hexdigest()

async def run_strategies_for_symbol(symbol: str, df_ltf, df_htf) -> List[dict]:
    out = []
    for s in STRATEGIES:
        try:
            sigs = s.generate_signals(df_ltf, df_htf)
            for sig in sigs:
                sig['symbol'] = symbol
                sig['strategy'] = s.name
                sig['timeframe'] = getattr(s, 'timeframe', '5m')
                sig.setdefault('candle_open', df_ltf.index[-1].isoformat())
                out.append(sig)
        except Exception as e:
            logger.warning("strategy.exec.error %s", {"strategy": getattr(s, 'name','?'), "error": str(e)})
    return out

async def evaluate_and_queue(symbol: str, df_ltf, df_htf):
    signals = await run_strategies_for_symbol(symbol, df_ltf, df_htf)
    if not signals: return
    features = {
        "close": float(df_ltf["close"].iloc[-1]),
        "atr": float((df_ltf["high"].iloc[-14:].max() - df_ltf["low"].iloc[-14:].min()) / 14.0),
        "rsi_like": float((df_ltf["close"].iloc[-1] - df_ltf["close"].iloc[-14]) / max(1e-9, df_ltf["close"].iloc[-14])),
    }
    await cache_features(symbol, features)
    score = fast_score([[features["close"], features["atr"], features["rsi_like"]]])
    for sig in signals:
        sig["model_score"] = score
        key = _dedup_key(sig)
        if not await dedup_try_set(key, DEDUP_TTL_SEC):
            logger.info("signal.duplicate_skipped %s", {"dedup_key": key}); continue
        sig["dedup_key"] = key
        await queue_signal(sig)
        logger.info("signal.queued %s", {"symbol": symbol, "strategy": sig["strategy"], "side": sig.get("side")})
