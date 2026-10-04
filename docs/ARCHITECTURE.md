# Architecture

```
+-----------------+   HTTPS/JSON    +--------------------+    SQLAlchemy    +--------------+
| React + Vite    | --------------> | FastAPI backend    | ---------------> | PostgreSQL   |
| Recharts, Axios |   JWT bearer    | routers / services |                  | users        |
+-----------------+                 |                    |                  | shipments    |
                                    |  prediction_service|                  | prediction_  |
                                    |    |      |        |                  |   history    |
                                    |    v      v        |                  | alerts       |
                                    |  ML      risk      |                  +--------------+
                                    |  model   service   |
                                    +----|---------------+
                                         v
                                  models/eta_model.joblib
```

## Components
| Component | Location | Responsibility |
|---|---|---|
| Frontend | `frontend/src` | Pages (login, dashboard, shipments, detail, predictions, alerts, analytics, what-if, settings), Axios client, auth context |
| API layer | `backend/app/routers` | HTTP endpoints, validation, auth dependency |
| Services | `backend/app/services` | `prediction_service` (ML -> risk -> store -> alert), `risk_service`, `analytics_service`, `seed_service` |
| ML | `backend/app/ml`, `ml/` | Feature list, model loader (`ETAPredictor`), training/evaluation scripts |
| Data | `backend/app/models` | SQLAlchemy tables |
| Config | `backend/app/config.py` | Environment-driven settings incl. risk thresholds |

## Prediction flow
1. Client sends shipment features + promised time.
2. `ETAPredictor` loads the joblib pipeline once; the pipeline one-hot-encodes categories and runs the RandomForest.
3. `risk_service` computes ratio -> LOW/MEDIUM/HIGH, the heuristic delay probability and the textual reasons.
4. `prediction_service` stores a `prediction_history` row (with error if actual is known), updates the shipment's cached latest prediction
   and creates (or refreshes) an unread alert if the shipment is active and HIGH risk.

## Database design
- `users(id, email, full_name, hashed_password, is_active, created_at)`
- `shipments(id, shipment_id UNIQUE, source, destination, distance_km, traffic_level, weather_condition, vehicle_type, hour_of_day, day_of_week, warehouse_delay_minutes, previous_route_delay_minutes, promised_delivery_minutes, actual_delivery_minutes, current_status, created_at, updated_at, + cached latest prediction columns)`
- `prediction_history(id, shipment_id FK NULL, predicted_delivery_minutes, promised_delivery_minutes, actual_delivery_minutes, prediction_error_minutes, risk_level, delay_probability, risk_reasons, input_features, created_at)` - `shipment_id` is nullable so ad-hoc predictions are stored too
- `alerts(id, shipment_id FK, risk_level, predicted_delivery_minutes, promised_delivery_minutes, predicted_eta, expected_delay_minutes, reason, message, is_read, created_at)`
Deleting a shipment cascades to its history and alerts.

## Design decisions (good viva answers)
- **Pipeline saved as one file** so training-time and prediction-time preprocessing can never differ.
- **Rule-based risk layer** instead of a second ML model: transparent, explainable, thresholds configurable.
- **Cached latest prediction on `shipments`** keeps list pages and dashboards fast; full detail stays in `prediction_history`.
- **SQLite fallback** only for easy local demos/tests; Docker uses PostgreSQL.
- **JWT in localStorage**: simple for a prototype; production should use httpOnly cookies and refresh tokens.
- **Seed data uses a different random seed than training data**, so predictions for seeded shipments are out-of-sample.

## Security
bcrypt password hashing, JWT (HS256, expiry from env), secrets from environment variables, CORS allow-list, Pydantic validation,
ORM (no raw SQL), generic 500 messages with stack traces only in logs. The demo account is for local use only.
