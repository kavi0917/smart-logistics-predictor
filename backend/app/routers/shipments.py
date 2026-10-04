import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.predictor import ModelNotAvailable
from app.models import Shipment, User
from app.schemas import PredictionHistoryOut, ShipmentCreate, ShipmentDetail, ShipmentOut, ShipmentUpdate
from app.services import prediction_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/shipments", tags=["Shipments"], dependencies=[Depends(get_current_user)])
logger = logging.getLogger("logistics.shipments")


def get_shipment_or_404(db: Session, ident: str) -> Shipment:
    """Accepts either the numeric primary key or the shipment code (e.g. L001)."""
    q = db.query(Shipment)
    shipment = q.filter(Shipment.id == int(ident)).first() if ident.isdigit() else q.filter(Shipment.shipment_id == ident).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


def _next_code(db: Session) -> str:
    n = db.query(Shipment).count() + 1
    while db.query(Shipment).filter(Shipment.shipment_id == f"L{n:03d}").first():
        n += 1
    return f"L{n:03d}"


def _try_predict(db: Session, shipment: Shipment):
    try:
        prediction_service.predict_for_shipment(db, shipment)
    except ModelNotAvailable as exc:
        logger.error("Prediction skipped: %s", exc)


@router.get("", response_model=list[ShipmentOut])
def list_shipments(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Shipment)
    if status_filter:
        q = q.filter(Shipment.current_status == status_filter.upper())
    if risk_level:
        q = q.filter(Shipment.risk_level == risk_level.upper())
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Shipment.shipment_id.ilike(like), Shipment.source.ilike(like), Shipment.destination.ilike(like)))
    return q.order_by(Shipment.created_at.desc(), Shipment.id.desc()).offset(offset).limit(limit).all()


@router.post("", response_model=ShipmentOut, status_code=status.HTTP_201_CREATED)
def create_shipment(body: ShipmentCreate, db: Session = Depends(get_db)):
    data = body.model_dump(mode="json")
    code = data.pop("shipment_id") or _next_code(db)
    if db.query(Shipment).filter(Shipment.shipment_id == code).first():
        raise HTTPException(status_code=400, detail=f"Shipment ID {code} already exists")
    shipment = Shipment(shipment_id=code, **data)
    db.add(shipment)
    db.flush()
    _try_predict(db, shipment)
    db.commit()
    db.refresh(shipment)
    logger.info("Shipment %s created", code)
    return shipment


@router.get("/{ident}", response_model=ShipmentDetail)
def get_shipment(ident: str, db: Session = Depends(get_db)):
    shipment = get_shipment_or_404(db, ident)
    out = ShipmentDetail.model_validate(shipment)
    history = []
    for p in shipment.predictions:
        item = PredictionHistoryOut.model_validate(p)
        item.shipment_code = shipment.shipment_id
        history.append(item)
    out.prediction_history = history
    return out


@router.put("/{ident}", response_model=ShipmentOut)
def update_shipment(ident: str, body: ShipmentUpdate, db: Session = Depends(get_db)):
    shipment = get_shipment_or_404(db, ident)
    changes = body.model_dump(mode="json", exclude_unset=True)
    for key, value in changes.items():
        if value is None and key not in ("actual_delivery_minutes",):
            continue
        setattr(shipment, key, value)
    # Auto-complete: recording an actual time on an active shipment marks it delivered/delayed
    if changes.get("actual_delivery_minutes") and "current_status" not in changes and shipment.current_status in ("PENDING", "IN_TRANSIT"):
        shipment.current_status = "DELIVERED" if shipment.actual_delivery_minutes <= shipment.promised_delivery_minutes else "DELAYED"
    db.flush()
    _try_predict(db, shipment)
    db.commit()
    db.refresh(shipment)
    logger.info("Shipment %s updated", shipment.shipment_id)
    return shipment


@router.delete("/{ident}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shipment(ident: str, db: Session = Depends(get_db)):
    shipment = get_shipment_or_404(db, ident)
    db.delete(shipment)
    db.commit()
    logger.info("Shipment %s deleted", ident)


@router.post("/{ident}/predict", response_model=ShipmentOut)
def run_prediction(ident: str, db: Session = Depends(get_db)):
    """Re-run the ML model for a stored shipment and save a new prediction history row."""
    shipment = get_shipment_or_404(db, ident)
    try:
        prediction_service.predict_for_shipment(db, shipment)
    except ModelNotAvailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    db.commit()
    db.refresh(shipment)
    return shipment
