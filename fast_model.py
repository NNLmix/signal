import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb
except Exception:
    lgb = None

MODEL_PATH = Path(__file__).parent / "models" / "fast_lgbm.txt"

class _FallbackDummy:
    def predict(self, X):
        n = X.shape[0] if hasattr(X, "shape") else len(X)
        return np.full((n,), 0.5, dtype=float)

_booster = None

def _load():
    global _booster
    if _booster is not None: return _booster
    if lgb is None:
        logger.warning("[fast_model] lightgbm not installed; using fallback dummy")
        _booster = _FallbackDummy(); return _booster
    try:
        if MODEL_PATH.exists():
            _booster = lgb.Booster(model_file=str(MODEL_PATH))
            logger.info("[fast_model] Loaded LightGBM booster from %s", MODEL_PATH)
        else:
            logger.warning("[fast_model] %s not found; using fallback dummy", MODEL_PATH)
            _booster = _FallbackDummy()
    except Exception as e:
        logger.warning("[fast_model] Failed to load booster (%s); using dummy", e)
        _booster = _FallbackDummy()
    return _booster

def fast_score(feature_rows) -> float:
    booster = _load()
    try:
        preds = booster.predict(feature_rows)
        if hasattr(preds, "__len__"): return float(np.mean(preds))
        return float(preds)
    except Exception as e:
        logger.warning("[fast_model] predict error: %s; fallback 0.5", e)
        return 0.5
