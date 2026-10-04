"""Create the demo user and sample shipments (idempotent)."""
import logging
import random
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import PROJECT_ROOT, get_settings
from app.models import Shipment, User
from app.services import prediction_service
from app.utils.security import hash_password

logger = logging.getLogger("logistics.seed")

DEMO_SHIPMENT = dict(
    shipment_id="L001", source="Chennai", destination="Coimbatore", distance_km=505, traffic_level="HIGH",
    weather_condition="RAIN", vehicle_type="TRUCK", hour_of_day=15, day_of_week=2, warehouse_delay_minutes=25,
    previous_route_delay_minutes=20, promised_delivery_minutes=900, current_status="IN_TRANSIT",
)


def ensure_demo_user(db: Session):
    s = get_settings()
    email = s.demo_user_email.lower()
    if not db.query(User).filter(User.email == email).first():
        db.add(User(email=email, full_name=s.demo_user_name, hashed_password=hash_password(s.demo_user_password)))
        db.commit()
        logger.info("Demo user %s created", email)


def seed_shipments(db: Session, n_completed: int = 45, n_active: int = 14, n_cancelled: int = 3, seed: int = 2026):
    """Insert sample shipments generated with the same rules as the training data but a DIFFERENT random seed,
    so predictions on them are genuinely out-of-sample."""
    if db.query(Shipment).count() > 0:
        return 0
    sys.path.insert(0, str(PROJECT_ROOT / "ml"))
    from generate_dataset import generate_rows  # noqa: E402

    rng = random.Random(seed)
    pool = generate_rows(n_rows=400, seed=seed, id_prefix="S")
    now = datetime.now(timezone.utc)
    rows = pool.to_dict("records")
    rng.shuffle(rows)
    completed = rows[:n_completed]
    # prefer problematic-looking shipments for the "active" group so the demo has alerts/risk
    candidates = [r for r in rows[n_completed:] if r["actual_delivery_minutes"] > r["promised_delivery_minutes"]]
    candidates += [r for r in rows[n_completed:] if r["actual_delivery_minutes"] <= r["promised_delivery_minutes"]]
    active = candidates[:n_active]
    used = {id(r) for r in completed + active}
    cancelled = [r for r in rows[n_completed:] if id(r) not in used][:n_cancelled]

    code = 1
    created = 0

    def add(row: dict, status: str, with_actual: bool, created_at: datetime):
        nonlocal code, created
        code += 1
        shipment = Shipment(
            shipment_id=f"L{code:03d}", source=row["source"], destination=row["destination"], distance_km=row["distance_km"],
            traffic_level=row["traffic_level"], weather_condition=row["weather_condition"], vehicle_type=row["vehicle_type"],
            hour_of_day=int(row["hour_of_day"]), day_of_week=int(row["day_of_week"]),
            warehouse_delay_minutes=int(row["warehouse_delay_minutes"]),
            previous_route_delay_minutes=int(row["previous_route_delay_minutes"]),
            promised_delivery_minutes=int(row["promised_delivery_minutes"]),
            actual_delivery_minutes=int(row["actual_delivery_minutes"]) if with_actual else None,
            current_status=status, created_at=created_at, updated_at=created_at,
        )
        db.add(shipment)
        db.flush()
        prediction_service.predict_for_shipment(db, shipment, created_at=created_at, create_alert=status in ("PENDING", "IN_TRANSIT"))
        created += 1

    # handcrafted demo shipment (matches the example in the project brief)
    demo = Shipment(**DEMO_SHIPMENT, created_at=now - timedelta(hours=2), updated_at=now)
    db.add(demo)
    db.flush()
    prediction_service.predict_for_shipment(db, demo)
    created += 1

    # oldest first so shipment codes increase with time
    completed_sorted = sorted(completed, key=lambda r: rng.random())
    for i, row in enumerate(completed_sorted):
        days_ago = 29 - (i * 29 / max(1, len(completed_sorted) - 1))
        ts = now - timedelta(days=days_ago, hours=rng.randint(0, 6))
        status = "DELIVERED" if row["actual_delivery_minutes"] <= row["promised_delivery_minutes"] else "DELAYED"
        add(row, status, True, ts)
    for i, row in enumerate(active):
        status = "IN_TRANSIT" if i < n_active - 3 else "PENDING"
        add(row, status, False, now - timedelta(hours=rng.randint(1, 20)))
    for row in cancelled:
        add(row, "CANCELLED", False, now - timedelta(days=rng.randint(1, 10)))
    db.commit()
    logger.info("Seeded %s shipments", created)
    return created


def seed_all(db: Session) -> int:
    ensure_demo_user(db)
    return seed_shipments(db)
