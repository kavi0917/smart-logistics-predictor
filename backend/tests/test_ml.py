"""Tests for the trained ML model file and predictor wrapper."""
import pytest

from app.config import get_settings
from app.ml.features import FEATURES
from app.ml.predictor import predictor

SAMPLE = {
    "distance_km": 120, "traffic_level": "MEDIUM", "weather_condition": "CLOUDY", "vehicle_type": "VAN",
    "hour_of_day": 10, "day_of_week": 1, "warehouse_delay_minutes": 5, "previous_route_delay_minutes": 3,
}


def test_model_file_exists():
    assert get_settings().resolved_model_path.exists()


def test_required_features_are_accepted_and_returns_numeric():
    assert set(FEATURES) == set(SAMPLE)
    minutes = predictor.predict_minutes(SAMPLE)
    assert isinstance(minutes, int) and minutes > 0


def test_prediction_never_negative_even_for_tiny_trip():
    assert predictor.predict_minutes({**SAMPLE, "distance_km": 0.5, "warehouse_delay_minutes": 0, "previous_route_delay_minutes": 0}) >= 1


def test_model_learned_expected_relationships():
    base = predictor.predict_minutes(SAMPLE)
    assert predictor.predict_minutes({**SAMPLE, "traffic_level": "HIGH"}) > base          # traffic slows delivery
    assert predictor.predict_minutes({**SAMPLE, "weather_condition": "STORM"}) > base     # storm slows delivery
    assert predictor.predict_minutes({**SAMPLE, "distance_km": 300}) > base               # distance matters
    assert predictor.predict_minutes({**SAMPLE, "warehouse_delay_minutes": 60}) > base    # warehouse delay adds time


def test_missing_feature_raises():
    incomplete = dict(SAMPLE)
    incomplete.pop("distance_km")
    with pytest.raises(KeyError):
        predictor.predict_minutes(incomplete)
