"""Train the ETA (delivery duration) model.

Pipeline: ColumnTransformer (one-hot for categoricals, passthrough numerics) + RandomForestRegressor.
The whole pipeline (preprocessing + model) is saved with joblib so the API only needs one file.
Run:  python ml/train_model.py
"""
import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "logistics_delivery_data.csv")
MODEL_PATH = os.path.join(ROOT, "models", "eta_model.joblib")
METRICS_PATH = os.path.join(ROOT, "models", "eta_model_metrics.json")

NUMERIC = ["distance_km", "hour_of_day", "day_of_week", "warehouse_delay_minutes", "previous_route_delay_minutes"]
CATEGORICAL = ["traffic_level", "weather_condition", "vehicle_type"]
FEATURES = NUMERIC + CATEGORICAL
TARGET = "actual_delivery_minutes"


def load_and_clean(path=DATA_PATH):
    df = pd.read_csv(path)
    df = df.dropna(subset=FEATURES + [TARGET]).drop_duplicates()
    df = df[(df[TARGET] > 0) & (df["distance_km"] > 0)]
    return df


def build_pipeline():
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", "passthrough", NUMERIC),
    ])
    model = RandomForestRegressor(n_estimators=100, max_depth=12, min_samples_leaf=5, random_state=42, n_jobs=-1)
    return Pipeline([("preprocess", pre), ("model", model)])


def main():
    df = load_and_clean()
    X, y = df[FEATURES], df[TARGET]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    pipe = build_pipeline().fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    mae = mean_absolute_error(y_te, pred)
    rmse = float(np.sqrt(mean_squared_error(y_te, pred)))
    r2 = r2_score(y_te, pred)
    print(f"Rows: {len(df)} (train {len(X_tr)}, test {len(X_te)})")
    print(f"MAE : {mae:.2f} minutes")
    print(f"RMSE: {rmse:.2f} minutes")
    print(f"R2  : {r2:.4f}")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    with open(METRICS_PATH, "w") as fh:
        json.dump({"mae": round(mae, 2), "rmse": round(rmse, 2), "r2": round(r2, 4),
                   "train_rows": len(X_tr), "test_rows": len(X_te), "algorithm": "RandomForestRegressor"}, fh, indent=2)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
