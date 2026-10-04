"""All analytics are computed from stored shipments / predictions (nothing hard-coded)."""
import math
from collections import Counter, OrderedDict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Alert, Shipment

ACTIVE = ("PENDING", "IN_TRANSIT")


def _completed(db: Session) -> list[Shipment]:
    return db.query(Shipment).filter(Shipment.actual_delivery_minutes.isnot(None), Shipment.current_status != "CANCELLED").all()


def summary(db: Session) -> dict:
    shipments = db.query(Shipment).all()
    total = len(shipments)
    by_status = Counter(s.current_status for s in shipments)
    completed = [s for s in shipments if s.actual_delivery_minutes is not None and s.current_status != "CANCELLED"]
    on_time = [s for s in completed if s.actual_delivery_minutes <= s.promised_delivery_minutes]
    active = [s for s in shipments if s.current_status in ACTIVE]
    errors = [abs(s.actual_delivery_minutes - s.predicted_delivery_minutes) for s in completed if s.predicted_delivery_minutes is not None]
    judged = [s for s in completed if s.predicted_delivery_minutes is not None]
    correct = [
        s for s in judged
        if (s.predicted_delivery_minutes <= s.promised_delivery_minutes) == (s.actual_delivery_minutes <= s.promised_delivery_minutes)
    ]
    return {
        "total_shipments": total,
        "active_shipments": len(active),
        "delivered_shipments": by_status.get("DELIVERED", 0),
        "delayed_shipments": by_status.get("DELAYED", 0),
        "cancelled_shipments": by_status.get("CANCELLED", 0),
        "on_time_shipments": len(on_time),
        "completed_shipments": len(completed),
        "on_time_percentage": round(100 * len(on_time) / len(completed), 1) if completed else 0.0,
        "at_risk_shipments": sum(1 for s in active if s.risk_level in ("MEDIUM", "HIGH")),
        "high_risk_shipments": sum(1 for s in active if s.risk_level == "HIGH"),
        "average_prediction_error": round(sum(errors) / len(errors), 1) if errors else 0.0,
        "on_time_prediction_accuracy": round(100 * len(correct) / len(judged), 1) if judged else 0.0,
    }


def dashboard_summary(db: Session) -> dict:
    data = summary(db)
    data["unread_alerts"] = db.query(Alert).filter(Alert.is_read.is_(False)).count()
    data["status_distribution"] = status_distribution(db)
    data["risk_distribution"] = risk_distribution(db)
    return data


def status_distribution(db: Session) -> dict:
    counts = Counter(s.current_status for s in db.query(Shipment).all())
    return {k: counts.get(k, 0) for k in ("PENDING", "IN_TRANSIT", "DELIVERED", "DELAYED", "CANCELLED")}


def risk_distribution(db: Session) -> dict:
    """Latest predicted risk of all non-cancelled shipments that have a prediction."""
    rows = db.query(Shipment).filter(Shipment.risk_level.isnot(None), Shipment.current_status != "CANCELLED").all()
    counts = Counter(s.risk_level for s in rows)
    return {k: counts.get(k, 0) for k in ("LOW", "MEDIUM", "HIGH")}


def performance(db: Session, days: int = 30) -> list[dict]:
    """Daily delivery performance for shipments created in the last `days` days (completed shipments only)."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    buckets: "OrderedDict[str, dict]" = OrderedDict()
    for offset in range(days, -1, -1):
        d = (datetime.now(timezone.utc) - timedelta(days=offset)).date().isoformat()
        buckets[d] = {"date": d, "completed": 0, "on_time": 0, "late": 0, "_err": []}
    for s in _completed(db):
        created = s.created_at if s.created_at.tzinfo else s.created_at.replace(tzinfo=timezone.utc)
        if created < since:
            continue
        b = buckets.get(created.date().isoformat())
        if b is None:
            continue
        b["completed"] += 1
        if s.actual_delivery_minutes <= s.promised_delivery_minutes:
            b["on_time"] += 1
        else:
            b["late"] += 1
        if s.predicted_delivery_minutes is not None:
            b["_err"].append(abs(s.actual_delivery_minutes - s.predicted_delivery_minutes))
    out = []
    for b in buckets.values():
        errs = b.pop("_err")
        b["on_time_percentage"] = round(100 * b["on_time"] / b["completed"], 1) if b["completed"] else None
        b["average_prediction_error"] = round(sum(errs) / len(errs), 1) if errs else None
        out.append(b)
    return out


def prediction_accuracy(db: Session, limit: int = 30) -> dict:
    done = [s for s in _completed(db) if s.predicted_delivery_minutes is not None]
    done.sort(key=lambda s: s.created_at)
    errors = [abs(s.actual_delivery_minutes - s.predicted_delivery_minutes) for s in done]
    n = len(errors)
    mae = sum(errors) / n if n else 0.0
    rmse = math.sqrt(sum(e * e for e in errors) / n) if n else 0.0
    within_15 = sum(1 for e in errors if e <= 15)
    within_10pct = sum(1 for s, e in zip(done, errors) if e <= 0.10 * s.actual_delivery_minutes)
    points = [
        {
            "shipment_code": s.shipment_id,
            "predicted": s.predicted_delivery_minutes,
            "actual": s.actual_delivery_minutes,
            "promised": s.promised_delivery_minutes,
            "error": abs(s.actual_delivery_minutes - s.predicted_delivery_minutes),
        }
        for s in done[-limit:]
    ]
    return {
        "evaluated_shipments": n,
        "mean_absolute_error": round(mae, 1),
        "rmse": round(rmse, 1),
        "within_15_minutes_pct": round(100 * within_15 / n, 1) if n else 0.0,
        "within_10_percent_pct": round(100 * within_10pct / n, 1) if n else 0.0,
        "on_time_prediction_accuracy": summary(db)["on_time_prediction_accuracy"],
        "points": points,
    }
