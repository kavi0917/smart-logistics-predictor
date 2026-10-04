"""Loads the trained scikit-learn pipeline (preprocessing + RandomForest) and predicts delivery minutes."""
import json
import logging
import threading

import joblib
import pandas as pd

from app.config import get_settings
from app.ml.features import FEATURES

logger = logging.getLogger("logistics.ml")


class ModelNotAvailable(RuntimeError):
    pass


class ETAPredictor:
    def __init__(self):
        self._pipeline = None
        self._lock = threading.Lock()

    @property
    def path(self):
        return get_settings().resolved_model_path

    def load(self):
        with self._lock:
            if self._pipeline is None:
                if not self.path.exists():
                    raise ModelNotAvailable(f"Model file not found at {self.path}. Run: python ml/train_model.py")
                self._pipeline = joblib.load(self.path)
                # single-row predictions are faster without joblib thread overhead
                try:
                    self._pipeline.named_steps["model"].n_jobs = 1
                except Exception:  # pragma: no cover
                    pass
                logger.info("Loaded ETA model from %s", self.path)
        return self._pipeline

    def is_loaded(self) -> bool:
        return self._pipeline is not None

    def predict_minutes(self, features: dict) -> int:
        """Return predicted delivery duration in whole minutes (never negative)."""
        pipe = self.load()
        row = pd.DataFrame([{name: features[name] for name in FEATURES}])
        value = float(pipe.predict(row)[0])
        return max(1, int(round(value)))

    def metrics(self) -> dict | None:
        metrics_path = self.path.with_name("eta_model_metrics.json")
        if metrics_path.exists():
            return json.loads(metrics_path.read_text())
        return None


predictor = ETAPredictor()
