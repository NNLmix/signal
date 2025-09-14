# fast_model.py
import os
from pathlib import Path
import joblib

# ---- resolve model path safely
BASE_DIR = Path(__file__).resolve().parent
env_path = os.getenv("FAST_MODEL_PATH", "").strip()
MODEL_PATH = Path(env_path) if env_path else (BASE_DIR / "models" / "fast_lgbm.pkl")
if MODEL_PATH.is_dir():  # guard against passing a directory by mistake
    MODEL_PATH = MODEL_PATH / "fast_lgbm.pkl"
if not MODEL_PATH.exists():
    alt = Path("/app/models/fast_lgbm.pkl")
    if alt.exists():
        MODEL_PATH = alt

# ---- local fallback model so the pipeline can run
class DummyModel:
    def __init__(self, score=0.5):
        self.score = float(score)
    def predict(self, X):
        try:
            n = len(X)
        except TypeError:
            n = 1
        return [self.score for _ in range(n)]

def _load_model():
    try:
        return joblib.load(str(MODEL_PATH))
    except Exception as e:
        # If the pickle was created with a different module path, unpickle may fail.
        # Fall back to a local dummy so the service can run.
        print(f"[fast_model] Warning: failed to load {MODEL_PATH} ({e}). Using DummyModel(0.5).")
        return DummyModel(0.5)

model = _load_model()

def fast_score(features):
    return float(model.predict([features])[0])
