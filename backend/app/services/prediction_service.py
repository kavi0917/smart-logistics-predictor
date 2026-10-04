"""Orchestrates: ML prediction -> risk layer -> storing history -> alert creation."""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.ml.features import FEATURES
from app.ml.predictor import predictor
from app.models import Alert, PredictionHistory, Shipment
from app.services import risk_service

logger = logging.getLogger("logistics.prediction")
ACTIVE_STATUSES = ("PENDING", "IN_TRANSIT")


def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def route_has_delay_history(db: Session, source: str | None, destination: str | None, exclude_id: int | None = None) -> bool:
    """True if at least 3 completed shipments exist on this route and >= 50% were late."""
    if not source or not destination:
        return False
    q = db.query(Shipment).filter(
        Shipment.source == source, Shipment.destination == destination, Shipment.actual_delivery_minutes.isnot(None)
    )
    if exclude_id:
        q = q.filter(Shipment.id != exclude_id)
    done = q.all()
    if len(done) < 3:
        return False
    late = sum(1 for s in done if s.actual_delivery_minutes > s.promised_delivery_minutes)
    return late / len(done) >= 0.5


def compute_prediction(features: dict, promised: int, departure: datetime | None = None, historical: bool = False) -> dict:
    """Pure calculation (no DB writes). Used by /predict, shipments and what-if."""
    feats = {k: (v.value if hasattr(v, "value") else v) for k, v in features.items() if k in FEATURES}
    minutes = predictor.predict_minutes(feats)
    departure = _as_utc(departure) if departure else datetime.now(timezone.utc)
    return {
        "predicted_delivery_minutes": minutes,
        "promised_delivery_minutes": promised,
        "predicted_eta": departure + timedelta(minutes=minutes),
        "expected_delay_minutes": max(0, minutes - promised),
        "risk_level": risk_service.classify_risk(minutes, promised),
        "delay_probability": risk_service.delay_probability(minutes, promised),
        "risk_reasons": risk_service.risk_reasons(feats, minutes, promised, historical),
    }


def store_prediction(
    db: Session, result: dict, features: dict, shipment: Shipment | None = None,
    actual: int | None = None, created_at: datetime | None = None, create_alert: bool = True,
) -> PredictionHistory:
    """Save a prediction to prediction_history; update the shipment cache; raise an alert if HIGH risk."""
    error = abs(actual - result["predicted_delivery_minutes"]) if actual is not None else None
    row = PredictionHistory(
        shipment_id=shipment.id if shipment else None,
        predicted_delivery_minutes=result["predicted_delivery_minutes"],
        promised_delivery_minutes=result["promised_delivery_minutes"],
        actual_delivery_minutes=actual,
        prediction_error_minutes=error,
        risk_level=result["risk_level"],
        delay_probability=result["delay_probability"],
        risk_reasons=result["risk_reasons"],
        input_features={k: (v.value if hasattr(v, "value") else v) for k, v in features.items() if k in FEATURES},
    )
    if created_at:
        row.created_at = created_at
    db.add(row)

    if shipment is not None:
        shipment.predicted_delivery_minutes = result["predicted_delivery_minutes"]
        shipment.predicted_eta = result["predicted_eta"]
        shipment.risk_level = result["risk_level"]
        shipment.delay_probability = result["delay_probability"]
        shipment.risk_reasons = result["risk_reasons"]
        if create_alert and result["risk_level"] == "HIGH" and shipment.current_status in ACTIVE_STATUSES:
            _create_alert_if_needed(db, shipment, result)
    db.flush()
    return row


def _create_alert_if_needed(db: Session, shipment: Shipment, result: dict):
    # Avoid duplicate unread alerts for the same shipment
    existing = db.query(Alert).filter(Alert.shipment_id == shipment.id, Alert.is_read.is_(False)).first()
    delay = result["expected_delay_minutes"]
    reason = ", ".join(result["risk_reasons"]) or "Predicted to exceed promised time"
    message = f"Shipment {shipment.shipment_id} is predicted to be delayed by approximately {delay} minutes."
    if existing:
        existing.predicted_delivery_minutes = result["predicted_delivery_minutes"]
        existing.predicted_eta = result["predicted_eta"]
        existing.expected_delay_minutes = delay
        existing.reason, existing.message = reason, message
        return
    db.add(Alert(
        shipment_id=shipment.id, risk_level=result["risk_level"],
        predicted_delivery_minutes=result["predicted_delivery_minutes"],
        promised_delivery_minutes=result["promised_delivery_minutes"],
        predicted_eta=result["predicted_eta"], expected_delay_minutes=delay, reason=reason, message=message,
    ))
    logger.info("Alert created for shipment %s (delay ~%s min)", shipment.shipment_id, delay)


SHIPMENT_FEATURE_FIELDS = FEATURES


def shipment_features(shipment: Shipment) -> dict:
    return {k: getattr(shipment, k) for k in SHIPMENT_FEATURE_FIELDS}


def predict_for_shipment(db: Session, shipment: Shipment, created_at: datetime | None = None, create_alert: bool = True) -> PredictionHistory:
    """Run the model for a stored shipment and persist the result."""
    feats = shipment_features(shipment)
    historical = route_has_delay_history(db, shipment.source, shipment.destination, exclude_id=shipment.id)
    departure = shipment.created_at or datetime.now(timezone.utc)
    result = compute_prediction(feats, shipment.promised_delivery_minutes, departure, historical)
    return store_prediction(
        db, result, feats, shipment=shipment, actual=shipment.actual_delivery_minutes,
        created_at=created_at, create_alert=create_alert,
    )
