import logging
from pathlib import Path
import numpy as np
import pickle
from config import FAST_MODEL_PATH

logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb
except Exception:
    lgb = None

MODEL_PATH = Path(FAST_MODEL_PATH) if FAST_MODEL_PATH else (Path(__file__).parent / "models" / "fast_lgbm.txt")

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
            try:
                if str(MODEL_PATH).endswith(".txt"):
                    _booster = lgb.Booster(model_file=str(MODEL_PATH))
                elif str(MODEL_PATH).endswith(".pkl"):
                    with open(MODEL_PATH, "rb") as f:
                        obj = pickle.load(f)
                    # obj can be Booster or sklearn LGBMModel
                    if hasattr(obj, "predict") and not isinstance(obj, (bytes, str)):
                        _booster = obj
                    else:
                        raise RuntimeError("Unsupported pickle content")
                else:
                    # try as native model_file by default
                    _booster = lgb.Booster(model_file=str(MODEL_PATH))
                logger.info("[fast_model] Loaded LightGBM model from %s", MODEL_PATH)
            except Exception as e:
                logger.warning("[fast_model] Can't load %s (%s); using dummy", MODEL_PATH, e)
                _booster = _FallbackDummy()
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
