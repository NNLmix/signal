import joblib
import numpy as np

model = joblib.load("models/fast_lgbm.pkl")

def fast_score(features: dict) -> float:
    # dict → вектор
    keys = ["last_price", "ema", "vwap", "imbalance", "vol_sum", "window_len"]
    x = np.array([features[k] for k in keys], dtype=float).reshape(1, -1)
    prob = model.predict(x)[0]
    return float(prob)
