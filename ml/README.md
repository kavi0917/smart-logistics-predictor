# Machine Learning

**Data is synthetic.** `generate_dataset.py` creates 2,500 shipments with plausible relationships plus noise:
base driving time = distance / vehicle speed; multiplied by traffic (1.0 / 1.18 / 1.45), weather (1.0 / 1.04 / 1.15 / 1.38) and peak-hour (1.08)
factors; plus warehouse delay, previous route delay, a fixed handling time and random noise. The *promised* time is a planner-style estimate that
ignores live conditions, so some shipments end up late. It is for academic prototyping only.

| Script | Purpose |
|---|---|
| `generate_dataset.py` | writes `data/logistics_delivery_data.csv` (seed 42) |
| `train_model.py` | clean -> encode (ColumnTransformer + OneHotEncoder) -> 80/20 split -> RandomForestRegressor -> MAE/RMSE/R2 -> saves `models/eta_model.joblib` and `models/eta_model_metrics.json` |
| `evaluate_model.py` | re-evaluates on the same held-out split and prints feature importances |

Features: distance_km, traffic_level, weather_condition, vehicle_type, hour_of_day, day_of_week, warehouse_delay_minutes, previous_route_delay_minutes.
Target: actual_delivery_minutes.

Latest run on the held-out 500 rows: **MAE 24.81 min, RMSE 40.14 min, R2 0.9777**.
The high R2 is expected because the data was generated from simple rules; real logistics data is much noisier. Distance dominates the feature importance.
