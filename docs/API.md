# API Reference

Base URL: `http://localhost:8000`. Interactive docs: `/docs`. All endpoints except `/health` and `/api/auth/login` need
`Authorization: Bearer <token>`.

## Errors
| Status | Meaning | Body |
|---|---|---|
| 400 | Invalid data | `{"detail":"Invalid data","errors":[{"field":"distance_km","message":"..."}]}` or `{"detail":"Shipment ID X already exists"}` |
| 401 | Missing / invalid token or wrong credentials | `{"detail":"Authentication required"}` |
| 404 | Not found | `{"detail":"Shipment not found"}` |
| 500 | Server error (stack trace only in server log) | `{"detail":"Internal server error"}` |
| 503 | Model file missing | `{"detail":"Model file not found ..."}` |

## Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/login` | Body `{"email","password"}` -> `{"access_token","token_type":"bearer",...}` |
| POST | `/api/auth/token` | Form login used by the Swagger "Authorize" button |
| GET | `/api/auth/me` | Current user |

## Shipments
| Method | Path | Description |
|---|---|---|
| GET | `/api/shipments?search=&status=&risk_level=&limit=&offset=` | List (newest first) |
| POST | `/api/shipments` | Create; a prediction (and alert, if HIGH risk and active) is generated automatically |
| GET | `/api/shipments/{id}` | `{id}` = numeric id **or** shipment code (e.g. `L001`); includes `prediction_history` |
| PUT | `/api/shipments/{id}` | Partial update; the prediction is recomputed |
| DELETE | `/api/shipments/{id}` | Delete (204) |
| POST | `/api/shipments/{id}/predict` | Re-run the model for a stored shipment |

Shipment fields: `shipment_id, source, destination, distance_km, traffic_level (LOW|MEDIUM|HIGH), weather_condition (CLEAR|CLOUDY|RAIN|STORM),
vehicle_type (VAN|TRUCK|BIKE|TEMPO), hour_of_day (0-23), day_of_week (0=Mon..6=Sun), warehouse_delay_minutes, previous_route_delay_minutes,
promised_delivery_minutes, actual_delivery_minutes, current_status (PENDING|IN_TRANSIT|DELIVERED|DELAYED|CANCELLED), created_at, updated_at`
plus the cached latest prediction: `predicted_delivery_minutes, predicted_eta, risk_level, delay_probability, risk_reasons`.

## Predictions
**POST `/api/predictions/predict`**
```json
{"distance_km":50,"traffic_level":"HIGH","weather_condition":"RAIN","vehicle_type":"TRUCK","hour_of_day":15,
 "day_of_week":2,"warehouse_delay_minutes":10,"previous_route_delay_minutes":5,"promised_delivery_minutes":90}
```
Optional: `shipment_id` (code, links the result to a shipment), `source`, `destination` (enables the "historical route delay" reason).
Response:
```json
{"predicted_delivery_minutes":144,"promised_delivery_minutes":90,"predicted_eta":"2026-10-04T11:35:42Z",
 "expected_delay_minutes":54,"risk_level":"HIGH","delay_probability":0.996,"risk_reasons":["High traffic","Rain conditions"]}
```
(The numbers come from the trained model, so they depend on the model file.) The result is always stored in `prediction_history`.

**POST `/api/predictions/what-if`** - body `{"base": <same as predict>, "overrides": {"traffic_level":"LOW", ...}}`. Allowed overrides:
`traffic_level, weather_condition, vehicle_type, warehouse_delay_minutes, previous_route_delay_minutes`. Returns `original`, `modified`,
`difference_minutes`, `risk_changed`. The model is executed twice; nothing is saved.

**GET `/api/predictions/history?shipment_id=L001&limit=100`** - stored predictions, newest first
(`prediction_error_minutes` is filled when the actual time is known).

## Alerts
| Method | Path | Description |
|---|---|---|
| GET | `/api/alerts?unread_only=true` | List alerts (shipment code, risk, predicted/promised time, ETA, reason, timestamp, read flag) |
| PATCH | `/api/alerts/{id}/read` | Mark one alert read |
| PATCH | `/api/alerts/read-all` | Mark all read |

## Dashboard & analytics
| Path | Description |
|---|---|
| GET `/api/dashboard/summary` | KPI cards + status and risk distributions + unread alerts |
| GET `/api/analytics/summary` | totals, on-time %, high-risk count, average prediction error, on-time prediction accuracy |
| GET `/api/analytics/risk-distribution` | `{"LOW":n,"MEDIUM":n,"HIGH":n}` (latest prediction per shipment) |
| GET `/api/analytics/status-distribution` | counts per status |
| GET `/api/analytics/performance?days=30` | one row per day: completed, on_time, late, on_time_percentage, average_prediction_error |
| GET `/api/analytics/prediction-accuracy?limit=30` | MAE, RMSE, within-15-min %, within-10% %, plus predicted-vs-actual points |
| GET `/api/settings` | active risk thresholds and model metrics (read-only) |

## Health
`GET /health` -> `{"status":"ok","database":true,"model_file":true}`.

## Risk logic (summary)
`ratio = predicted / promised`. LOW if ratio <= 1.00, MEDIUM if <= 1.15, HIGH above (configurable).
`delay_probability = 1 / (1 + exp(-(predicted - promised) / scale))`, `scale = max(10, 0.08 x promised)`.
This is a heuristic score between 0 and 1 and is **not statistically calibrated**.
