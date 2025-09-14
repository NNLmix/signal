import joblib
import lightgbm as lgb
import pandas as pd

# Загружаем исторические сигналы и их outcome (надо собрать заранее в Supabase)
df = pd.read_csv("signals_history.csv")  
# Структура: features..., outcome (1=успех, 0=провал)

X = df.drop(columns=["outcome"])
y = df["outcome"]

train_data = lgb.Dataset(X, label=y)
params = {
    "objective": "binary",
    "metric": "binary_error",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": -1,
}
model = lgb.train(params, train_data, num_boost_round=200)

joblib.dump(model, "models/fast_lgbm.pkl")
print("✅ Model saved")
