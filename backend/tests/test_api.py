"""API integration tests (FastAPI TestClient + real DB + real ML model)."""
from conftest import DEMO_EMAIL, DEMO_PASSWORD, VALID_PREDICTION


# ---------- health & auth ----------
def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["database"] is True and body["model_file"] is True


def test_login_success_returns_jwt(client):
    r = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer" and len(r.json()["access_token"]) > 20


def test_login_wrong_password_rejected(client):
    r = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": "wrong"})
    assert r.status_code == 401


def test_protected_endpoint_requires_token(client):
    r = client.get("/api/shipments")
    assert r.status_code == 401
    assert r.json()["detail"] == "Authentication required"


def test_invalid_token_rejected(client):
    r = client.get("/api/shipments", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


# ---------- shipments ----------
def test_seeded_shipments_are_listed(client, auth_headers):
    r = client.get("/api/shipments", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 50
    assert any(s["shipment_id"] == "L001" for s in r.json())


def test_create_and_retrieve_shipment_with_prediction(client, auth_headers, new_shipment_payload):
    created = client.post("/api/shipments", json=new_shipment_payload, headers=auth_headers)
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["shipment_id"].startswith("L")
    assert data["predicted_delivery_minutes"] > 0          # prediction generated automatically
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    detail = client.get(f"/api/shipments/{data['shipment_id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert len(detail.json()["prediction_history"]) == 1


def test_update_shipment_recomputes_prediction(client, auth_headers, new_shipment_payload):
    sid = client.post("/api/shipments", json=new_shipment_payload, headers=auth_headers).json()["shipment_id"]
    before = client.get(f"/api/shipments/{sid}", headers=auth_headers).json()["predicted_delivery_minutes"]
    r = client.put(f"/api/shipments/{sid}", json={"traffic_level": "HIGH", "weather_condition": "STORM"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["predicted_delivery_minutes"] > before
    assert len(client.get(f"/api/shipments/{sid}", headers=auth_headers).json()["prediction_history"]) == 2


def test_recording_actual_time_computes_prediction_error(client, auth_headers, new_shipment_payload):
    sid = client.post("/api/shipments", json=new_shipment_payload, headers=auth_headers).json()["shipment_id"]
    r = client.put(f"/api/shipments/{sid}", json={"actual_delivery_minutes": 250}, headers=auth_headers)
    assert r.json()["current_status"] == "DELIVERED"
    latest = client.get(f"/api/shipments/{sid}", headers=auth_headers).json()["prediction_history"][0]
    assert latest["actual_delivery_minutes"] == 250
    assert latest["prediction_error_minutes"] == abs(250 - latest["predicted_delivery_minutes"])


def test_delete_shipment(client, auth_headers, new_shipment_payload):
    sid = client.post("/api/shipments", json=new_shipment_payload, headers=auth_headers).json()["shipment_id"]
    assert client.delete(f"/api/shipments/{sid}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/shipments/{sid}", headers=auth_headers).status_code == 404


def test_shipment_not_found_returns_404(client, auth_headers):
    r = client.get("/api/shipments/DOES-NOT-EXIST", headers=auth_headers)
    assert r.status_code == 404 and r.json()["detail"] == "Shipment not found"


def test_invalid_shipment_data_returns_400(client, auth_headers, new_shipment_payload):
    bad = {**new_shipment_payload, "distance_km": -5, "traffic_level": "EXTREME", "hour_of_day": 30}
    r = client.post("/api/shipments", json=bad, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid data" and len(r.json()["errors"]) >= 3


def test_duplicate_shipment_id_rejected(client, auth_headers, new_shipment_payload):
    payload = {**new_shipment_payload, "shipment_id": "DUP-1"}
    assert client.post("/api/shipments", json=payload, headers=auth_headers).status_code == 201
    assert client.post("/api/shipments", json=payload, headers=auth_headers).status_code == 400


# ---------- predictions ----------
def test_predict_endpoint_returns_valid_result(client, auth_headers):
    r = client.post("/api/predictions/predict", json=VALID_PREDICTION, headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body["predicted_delivery_minutes"], int) and body["predicted_delivery_minutes"] > 0
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert 0.0 <= body["delay_probability"] <= 1.0
    assert "High traffic" in body["risk_reasons"] and "Rain conditions" in body["risk_reasons"]
    assert body["predicted_eta"]


def test_predictions_respond_to_inputs(client, auth_headers):
    calm = {**VALID_PREDICTION, "traffic_level": "LOW", "weather_condition": "CLEAR", "warehouse_delay_minutes": 0, "previous_route_delay_minutes": 0}
    bad = client.post("/api/predictions/predict", json=VALID_PREDICTION, headers=auth_headers).json()
    good = client.post("/api/predictions/predict", json=calm, headers=auth_headers).json()
    assert bad["predicted_delivery_minutes"] > good["predicted_delivery_minutes"]


def test_prediction_is_stored_in_history(client, auth_headers):
    before = len(client.get("/api/predictions/history?limit=1000", headers=auth_headers).json())
    client.post("/api/predictions/predict", json=VALID_PREDICTION, headers=auth_headers)
    after = client.get("/api/predictions/history?limit=1000", headers=auth_headers).json()
    assert len(after) == before + 1


def test_predict_validation_error(client, auth_headers):
    r = client.post("/api/predictions/predict", json={**VALID_PREDICTION, "vehicle_type": "SPACESHIP"}, headers=auth_headers)
    assert r.status_code == 400


def test_what_if_reruns_model_and_does_not_store(client, auth_headers):
    before = len(client.get("/api/predictions/history?limit=1000", headers=auth_headers).json())
    r = client.post("/api/predictions/what-if", json={"base": VALID_PREDICTION, "overrides": {"traffic_level": "LOW", "warehouse_delay_minutes": 0}}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["modified"]["predicted_delivery_minutes"] < body["original"]["predicted_delivery_minutes"]
    assert body["difference_minutes"] == body["modified"]["predicted_delivery_minutes"] - body["original"]["predicted_delivery_minutes"]
    assert len(client.get("/api/predictions/history?limit=1000", headers=auth_headers).json()) == before


# ---------- alerts ----------
def test_alerts_exist_for_high_risk_and_can_be_marked_read(client, auth_headers):
    alerts = client.get("/api/alerts", headers=auth_headers).json()
    assert len(alerts) > 0
    alert = next(a for a in alerts if not a["is_read"])
    assert alert["risk_level"] == "HIGH" and "predicted to be delayed" in alert["message"]
    r = client.patch(f"/api/alerts/{alert['id']}/read", headers=auth_headers)
    assert r.status_code == 200 and r.json()["is_read"] is True


def test_high_risk_shipment_creation_raises_alert(client, auth_headers):
    payload = {
        "source": "Chennai", "destination": "Coimbatore", "distance_km": 500, "traffic_level": "HIGH",
        "weather_condition": "STORM", "vehicle_type": "TRUCK", "hour_of_day": 18, "day_of_week": 3,
        "warehouse_delay_minutes": 40, "previous_route_delay_minutes": 30, "promised_delivery_minutes": 700,
        "current_status": "IN_TRANSIT", "shipment_id": "ALERT-TEST",
    }
    s = client.post("/api/shipments", json=payload, headers=auth_headers).json()
    assert s["risk_level"] == "HIGH"
    alerts = client.get("/api/alerts", headers=auth_headers).json()
    assert any(a["shipment_code"] == "ALERT-TEST" for a in alerts)


def test_alert_not_found(client, auth_headers):
    assert client.patch("/api/alerts/999999/read", headers=auth_headers).status_code == 404


# ---------- analytics ----------
def test_dashboard_and_analytics_summary_are_consistent(client, auth_headers):
    summary = client.get("/api/analytics/summary", headers=auth_headers).json()
    dash = client.get("/api/dashboard/summary", headers=auth_headers).json()
    shipments = client.get("/api/shipments?limit=1000", headers=auth_headers).json()
    assert summary["total_shipments"] == len(shipments) == dash["total_shipments"]
    assert 0 <= summary["on_time_percentage"] <= 100
    assert summary["average_prediction_error"] >= 0
    assert sum(dash["status_distribution"].values()) == summary["total_shipments"]


def test_risk_distribution_and_performance(client, auth_headers):
    risk = client.get("/api/analytics/risk-distribution", headers=auth_headers).json()
    assert set(risk) == {"LOW", "MEDIUM", "HIGH"} and sum(risk.values()) > 0
    perf = client.get("/api/analytics/performance?days=30", headers=auth_headers).json()
    assert len(perf) == 31 and sum(p["completed"] for p in perf) > 0


def test_prediction_accuracy_metrics(client, auth_headers):
    acc = client.get("/api/analytics/prediction-accuracy", headers=auth_headers).json()
    assert acc["evaluated_shipments"] > 0 and acc["mean_absolute_error"] >= 0
    assert acc["rmse"] >= acc["mean_absolute_error"]
    assert all({"predicted", "actual"} <= set(p) for p in acc["points"])


def test_settings_endpoint_exposes_thresholds(client, auth_headers):
    r = client.get("/api/settings", headers=auth_headers).json()
    assert r["risk_thresholds"]["high_if_predicted_over_promised_ratio"] > r["risk_thresholds"]["medium_if_predicted_over_promised_ratio"]
    assert r["model"]["file_exists"] is True
