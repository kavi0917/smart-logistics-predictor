"""Evaluate the saved model on the dataset and print metrics + feature importances."""
import os
import sys
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_model import FEATURES, TARGET, MODEL_PATH, load_and_clean  # noqa: E402


def main():
    if not os.path.exists(MODEL_PATH):
        sys.exit("Model not found. Run: python ml/train_model.py")
    pipe = joblib.load(MODEL_PATH)
    df = load_and_clean()
    # Same split as train_model.py so we evaluate on the held-out 20% test set only
    _, X_te, _, y = train_test_split(df[FEATURES], df[TARGET], test_size=0.2, random_state=42)
    pred = pipe.predict(X_te)
    print(f"MAE : {mean_absolute_error(y, pred):.2f}\nRMSE: {np.sqrt(mean_squared_error(y, pred)):.2f}\nR2  : {r2_score(y, pred):.4f}")
    names = pipe.named_steps["preprocess"].get_feature_names_out()
    imp = sorted(zip(names, pipe.named_steps["model"].feature_importances_), key=lambda t: -t[1])
    print("\nTop feature importances:")
    for n, v in imp[:8]:
        print(f"  {n:40s} {v:.3f}")


if __name__ == "__main__":
    main()
