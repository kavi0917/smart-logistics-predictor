import os
import sys
import tempfile
from pathlib import Path

# Configure the app for testing BEFORE it is imported.
_tmp = tempfile.mkdtemp(prefix="logistics_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SEED_ON_STARTUP"] = "true"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

DEMO_EMAIL = "admin@logistics.local"
DEMO_PASSWORD = "Admin@123"

VALID_PREDICTION = {
    "distance_km": 50, "traffic_level": "HIGH", "weather_condition": "RAIN", "vehicle_type": "TRUCK",
    "hour_of_day": 15, "day_of_week": 2, "warehouse_delay_minutes": 10, "previous_route_delay_minutes": 5,
    "promised_delivery_minutes": 90,
}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # runs startup: create tables, demo user, seed data
        yield c


@pytest.fixture(scope="session")
def auth_headers(client):
    r = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def new_shipment_payload():
    return {
        "source": "Chennai", "destination": "Vellore", "distance_km": 140, "traffic_level": "MEDIUM",
        "weather_condition": "CLOUDY", "vehicle_type": "VAN", "hour_of_day": 9, "day_of_week": 1,
        "warehouse_delay_minutes": 12, "previous_route_delay_minutes": 6, "promised_delivery_minutes": 260,
    }
