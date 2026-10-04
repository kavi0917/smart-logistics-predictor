from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analytics_service
from app.utils.deps import get_current_user

analytics_router = APIRouter(prefix="/api/analytics", tags=["Analytics"], dependencies=[Depends(get_current_user)])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)])


@analytics_router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return analytics_service.summary(db)


@analytics_router.get("/risk-distribution")
def risk_distribution(db: Session = Depends(get_db)):
    return analytics_service.risk_distribution(db)


@analytics_router.get("/status-distribution")
def status_distribution(db: Session = Depends(get_db)):
    return analytics_service.status_distribution(db)


@analytics_router.get("/performance")
def performance(days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)):
    return analytics_service.performance(db, days)


@analytics_router.get("/prediction-accuracy")
def prediction_accuracy(limit: int = Query(default=30, ge=1, le=200), db: Session = Depends(get_db)):
    return analytics_service.prediction_accuracy(db, limit)


@dashboard_router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    return analytics_service.dashboard_summary(db)
