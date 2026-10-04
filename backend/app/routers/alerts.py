from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.schemas import AlertOut
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["Alerts"], dependencies=[Depends(get_current_user)])


def _to_out(alert: Alert) -> AlertOut:
    out = AlertOut.model_validate(alert)
    out.shipment_code = alert.shipment.shipment_id
    return out


@router.get("", response_model=list[AlertOut])
def list_alerts(unread_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(Alert)
    if unread_only:
        q = q.filter(Alert.is_read.is_(False))
    return [_to_out(a) for a in q.order_by(Alert.created_at.desc(), Alert.id.desc()).all()]


@router.patch("/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    count = db.query(Alert).filter(Alert.is_read.is_(False)).update({"is_read": True})
    db.commit()
    return {"updated": count}


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return _to_out(alert)
