# fast_model.py
import os
from pathlib import Path
import joblib

# Project root (where fast_model.py resides)
BASE_DIR = Path(__file__).resolve().parent

# Preferred path via env, else fall back to relative-to-file
MODEL_PATH = Path(os.getenv("FAST_MODEL_PATH", ""))  # allow override
if not MODEL_PATH:
    MODEL_PATH = BASE_DIR / "models" / "fast_lgbm.pkl"

if not MODEL_PATH.exists():
    # try the /app path explicitly as a second fallback
    alt = Path("/app/models/fast_lgbm.pkl")
    if alt.exists():
        MODEL_PATH = alt

if not MODEL_PATH.exists():
    # Helpful diagnostics: list what we actually have
    models_dir = BASE_DIR / "models"
    candidates = [
        str(MODEL_PATH),
        str(alt) if 'alt' in locals() else None,
        str(models_dir),
    ]
    listing = []
    try:
        listing = [p.name for p in models_dir.iterdir()]
    except Exception:
        pass
    raise FileNotFoundError(
        "Model file not found.\n"
        f"Checked: {', '.join([c for c in candidates if c])}\n"
        f"models/ dir listing: {listing or 'unavailable'}\n"
        "Ensure Dockerfile copies models/:  COPY models/ /app/models/"
    )

model = joblib.load(str(MODEL_PATH))

def fast_score(features):
    return float(model.predict([features])[0])
