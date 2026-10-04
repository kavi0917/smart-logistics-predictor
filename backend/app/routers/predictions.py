from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.predictor import ModelNotAvailable
from app.models import PredictionHistory, Shipment
from app.routers.shipments import get_shipment_or_404
from app.schemas import PredictionHistoryOut, PredictionRequest, PredictionResult, WhatIfRequest, WhatIfResponse
from app.services import prediction_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/predictions", tags=["Predictions"], dependencies=[Depends(get_current_user)])

FEATURE_KEYS = [
    "distance_km", "traffic_level", "weather_condition", "vehicle_type", "hour_of_day", "day_of_week",
    "warehouse_delay_minutes", "previous_route_delay_minutes",
]


def _features(req: PredictionRequest) -> dict:
    return {k: getattr(req, k) for k in FEATURE_KEYS}


@router.post("/predict", response_model=PredictionResult)
def predict(body: PredictionRequest, db: Session = Depends(get_db)):
    """Predict ETA + delay risk. The result is always stored in prediction_history.
    If `shipment_id` (code) is supplied the result is linked to that shipment."""
    shipment: Optional[Shipment] = get_shipment_or_404(db, body.shipment_id) if body.shipment_id else None
    source = body.source or (shipment.source if shipment else None)
    destination = body.destination or (shipment.destination if shipment else None)
    try:
        historical = prediction_service.route_has_delay_history(db, source, destination, shipment.id if shipment else None)
        feats = _features(body)
        result = prediction_service.compute_prediction(feats, body.promised_delivery_minutes, historical=historical)
    except ModelNotAvailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    prediction_service.store_prediction(db, result, feats, shipment=shipment, actual=shipment.actual_delivery_minutes if shipment else None)
    db.commit()
    return result


@router.post("/what-if", response_model=WhatIfResponse)
def what_if(body: WhatIfRequest, db: Session = Depends(get_db)):
    """Re-run the ML model with modified inputs. Nothing is saved."""
    base = _features(body.base)
    applied = {k: (v.value if hasattr(v, "value") else v) for k, v in body.overrides.model_dump(exclude_none=True).items()}
    modified = {**base, **body.overrides.model_dump(exclude_none=True)}
    try:
        historical = prediction_service.route_has_delay_history(db, body.base.source, body.base.destination)
        orig = prediction_service.compute_prediction(base, body.base.promised_delivery_minutes, historical=historical)
        new = prediction_service.compute_prediction(modified, body.base.promised_delivery_minutes, historical=historical)
    except ModelNotAvailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return WhatIfResponse(
        original=orig, modified=new,
        difference_minutes=new["predicted_delivery_minutes"] - orig["predicted_delivery_minutes"],
        risk_changed=orig["risk_level"] != new["risk_level"], applied_overrides=applied,
    )


@router.get("/history", response_model=list[PredictionHistoryOut])
def history(
    shipment_id: Optional[str] = None, limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)
):
    q = db.query(PredictionHistory, Shipment.shipment_id).outerjoin(Shipment, PredictionHistory.shipment_id == Shipment.id)
    if shipment_id:
        q = q.filter(Shipment.shipment_id == shipment_id)
    rows = q.order_by(PredictionHistory.created_at.desc(), PredictionHistory.id.desc()).limit(limit).all()
    out = []
    for p, code in rows:
        item = PredictionHistoryOut.model_validate(p)
        item.shipment_code = code
        out.append(item)
    return out
