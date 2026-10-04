"""Generate a SYNTHETIC logistics delivery dataset (academic prototype only).

The data is NOT real. It is generated from simple, realistic rules + noise:
  * longer distance -> longer delivery
  * HIGH traffic, RAIN/STORM, peak hours, warehouse delay, previous route delay -> longer delivery
  * vehicle type changes average speed
Run:  python ml/generate_dataset.py
"""
import os
import numpy as np
import pandas as pd

SEED = 42
N_ROWS = 2500
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "logistics_delivery_data.csv")

CITY_PAIRS = [
    ("Chennai", "Coimbatore", 505), ("Chennai", "Bengaluru", 345), ("Coimbatore", "Madurai", 215),
    ("Chennai", "Madurai", 460), ("Coimbatore", "Salem", 165), ("Chennai", "Vellore", 140),
    ("Bengaluru", "Hosur", 40), ("Coimbatore", "Tiruppur", 50), ("Chennai", "Kanchipuram", 72),
    ("Madurai", "Trichy", 135), ("Salem", "Erode", 65), ("Coimbatore", "Pollachi", 40),
    ("Chennai", "Pondicherry", 150), ("Trichy", "Thanjavur", 60), ("Erode", "Coimbatore", 100),
]
VEHICLE_SPEED = {"BIKE": 32, "VAN": 45, "TEMPO": 38, "TRUCK": 42}  # km/h average
TRAFFIC_MULT = {"LOW": 1.0, "MEDIUM": 1.18, "HIGH": 1.45}
WEATHER_MULT = {"CLEAR": 1.0, "CLOUDY": 1.04, "RAIN": 1.15, "STORM": 1.38}


def generate_rows(n_rows=N_ROWS, seed=SEED, id_prefix="H"):
    """Return a DataFrame of synthetic shipments. Also used by the database seed script."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_rows):
        src, dst, base_km = CITY_PAIRS[rng.integers(len(CITY_PAIRS))]
        if rng.random() < 0.5:
            src, dst = dst, src
        distance = round(float(base_km * rng.uniform(0.95, 1.1)), 1)
        vehicle = rng.choice(list(VEHICLE_SPEED), p=[0.15, 0.35, 0.2, 0.3])
        if vehicle == "BIKE" and distance > 80:
            vehicle = "VAN"
        hour = int(rng.integers(0, 24))
        dow = int(rng.integers(0, 7))  # 0 = Monday
        peak = hour in (8, 9, 10, 17, 18, 19, 20)
        traffic = rng.choice(["LOW", "MEDIUM", "HIGH"], p=[0.25, 0.4, 0.35] if peak else [0.5, 0.35, 0.15])
        weather = rng.choice(["CLEAR", "CLOUDY", "RAIN", "STORM"], p=[0.5, 0.25, 0.18, 0.07])
        warehouse = int(max(0, rng.gamma(2.0, 8.0)))
        prev = int(max(0, rng.gamma(1.6, 7.0) * (1.5 if traffic == "HIGH" else 1)))

        drive = distance / VEHICLE_SPEED[vehicle] * 60
        mult = TRAFFIC_MULT[traffic] * WEATHER_MULT[weather] * (1.08 if peak else 1.0)
        if dow >= 5:
            mult *= 0.95
        actual = drive * mult + 0.9 * warehouse + 0.5 * prev + 12 + rng.normal(0, 0.04 * drive + 5)
        actual = int(max(10, round(actual)))
        # Promised time: a planner's estimate that ignores most live conditions
        promised = int(round(drive * 1.32 + 30 + 0.7 * warehouse + rng.normal(0, 10)))
        promised = max(15, promised)
        status = "DELIVERED" if actual <= promised else "DELAYED"
        rows.append(dict(
            shipment_id=f"{id_prefix}{i + 1:04d}", source=src, destination=dst, distance_km=distance,
            traffic_level=traffic, weather_condition=weather, vehicle_type=vehicle,
            hour_of_day=hour, day_of_week=dow, warehouse_delay_minutes=warehouse,
            previous_route_delay_minutes=prev, promised_delivery_minutes=promised,
            actual_delivery_minutes=actual, current_status=status,
        ))
    return pd.DataFrame(rows)


def main():
    df = generate_rows()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df)} rows to {OUT}; delayed share = {(df.current_status == 'DELAYED').mean():.1%}")


if __name__ == "__main__":
    main()
