"""Feature names expected by the trained pipeline (must match ml/train_model.py)."""
NUMERIC = ["distance_km", "hour_of_day", "day_of_week", "warehouse_delay_minutes", "previous_route_delay_minutes"]
CATEGORICAL = ["traffic_level", "weather_condition", "vehicle_type"]
FEATURES = NUMERIC + CATEGORICAL
