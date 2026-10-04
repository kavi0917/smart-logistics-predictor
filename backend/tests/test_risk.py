"""Unit tests for the rule-based delay-risk layer."""
from app.services import risk_service

BASE = {
    "distance_km": 50, "traffic_level": "LOW", "weather_condition": "CLEAR", "vehicle_type": "VAN",
    "hour_of_day": 13, "day_of_week": 2, "warehouse_delay_minutes": 0, "previous_route_delay_minutes": 0,
}


def test_low_risk_when_predicted_within_promised():
    assert risk_service.classify_risk(80, 100) == "LOW"
    assert risk_service.classify_risk(100, 100) == "LOW"


def test_medium_risk_when_slightly_late():
    assert risk_service.classify_risk(108, 100) == "MEDIUM"


def test_high_risk_when_significantly_late():
    assert risk_service.classify_risk(130, 100) == "HIGH"


def test_delay_probability_is_monotonic_and_bounded():
    probs = [risk_service.delay_probability(p, 100) for p in (50, 90, 100, 115, 150, 300)]
    assert probs == sorted(probs)
    assert all(0.0 <= p <= 1.0 for p in probs)
    assert risk_service.delay_probability(60, 100) < 0.1 < 0.9 < risk_service.delay_probability(160, 100)


def test_reasons_reflect_inputs():
    feats = {**BASE, "traffic_level": "HIGH", "weather_condition": "RAIN", "distance_km": 400,
             "warehouse_delay_minutes": 30, "previous_route_delay_minutes": 25, "hour_of_day": 18}
    reasons = risk_service.risk_reasons(feats, 600, 400, historical_route_delay=True)
    for expected in ("High traffic", "Rain conditions", "Long distance", "Warehouse processing delay",
                     "Previous route delay", "Peak-hour travel", "Historical route delay"):
        assert expected in reasons


def test_no_reasons_for_calm_on_time_shipment():
    assert risk_service.risk_reasons(BASE, 80, 100) == []
