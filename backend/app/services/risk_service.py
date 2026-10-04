"""Rule-based delay-risk layer on top of the ML ETA prediction.

Risk level compares predicted vs promised delivery time (thresholds live in config):
    ratio = predicted / promised
    LOW    : ratio <= risk_medium_ratio   (on or before the promised time)
    MEDIUM : risk_medium_ratio < ratio <= risk_high_ratio  (slightly late)
    HIGH   : ratio > risk_high_ratio      (significantly late)

delay_probability is a simple logistic score of how far the predicted time is beyond the promise:
    p = 1 / (1 + exp(-(predicted - promised) / scale)),  scale = max(min_scale, ratio_scale * promised)
It is a heuristic "risk score between 0 and 1". It is NOT a statistically calibrated probability.
"""
import math

from app.config import get_settings


def classify_risk(predicted: float, promised: float) -> str:
    s = get_settings()
    ratio = predicted / max(promised, 1)
    if ratio > s.risk_high_ratio:
        return "HIGH"
    if ratio > s.risk_medium_ratio:
        return "MEDIUM"
    return "LOW"


def delay_probability(predicted: float, promised: float) -> float:
    s = get_settings()
    scale = max(s.probability_min_scale_minutes, s.probability_scale_ratio * promised)
    z = (predicted - promised) / scale
    z = max(-30.0, min(30.0, z))
    return round(1.0 / (1.0 + math.exp(-z)), 3)


def risk_reasons(features: dict, predicted: float, promised: float, historical_route_delay: bool = False) -> list[str]:
    """Human-readable reasons, derived directly from the input features and thresholds."""
    s = get_settings()
    reasons: list[str] = []
    if features["traffic_level"] == "HIGH":
        reasons.append("High traffic")
    if features["weather_condition"] == "STORM":
        reasons.append("Storm conditions")
    elif features["weather_condition"] == "RAIN":
        reasons.append("Rain conditions")
    if features["distance_km"] >= s.long_distance_km:
        reasons.append("Long distance")
    if features["warehouse_delay_minutes"] >= s.warehouse_delay_threshold:
        reasons.append("Warehouse processing delay")
    if features["previous_route_delay_minutes"] >= s.previous_delay_threshold:
        reasons.append("Previous route delay")
    if features["hour_of_day"] in s.peak_hour_list:
        reasons.append("Peak-hour travel")
    if historical_route_delay:
        reasons.append("Historical route delay")
    if not reasons and predicted > promised:
        reasons.append("Promised time is tight for this route")
    return reasons
