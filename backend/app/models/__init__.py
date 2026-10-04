from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)  # business code, e.g. L001
    source: Mapped[str] = mapped_column(String(120))
    destination: Mapped[str] = mapped_column(String(120))
    distance_km: Mapped[float] = mapped_column(Float)
    traffic_level: Mapped[str] = mapped_column(String(10))
    weather_condition: Mapped[str] = mapped_column(String(10))
    vehicle_type: Mapped[str] = mapped_column(String(10))
    hour_of_day: Mapped[int] = mapped_column(Integer)
    day_of_week: Mapped[int] = mapped_column(Integer)
    warehouse_delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    previous_route_delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    promised_delivery_minutes: Mapped[int] = mapped_column(Integer)
    actual_delivery_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_status: Mapped[str] = mapped_column(String(15), default="PENDING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Latest prediction is cached on the shipment so lists/dashboards are fast.
    predicted_delivery_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    predicted_eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    delay_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)

    predictions = relationship(
        "PredictionHistory", back_populates="shipment", cascade="all, delete-orphan",
        order_by="PredictionHistory.created_at.desc()",
    )
    alerts = relationship("Alert", back_populates="shipment", cascade="all, delete-orphan")


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Nullable: ad-hoc predictions made from the Predictions page are not tied to a shipment.
    shipment_id: Mapped[int | None] = mapped_column(ForeignKey("shipments.id", ondelete="CASCADE"), nullable=True, index=True)
    predicted_delivery_minutes: Mapped[int] = mapped_column(Integer)
    promised_delivery_minutes: Mapped[int] = mapped_column(Integer)
    actual_delivery_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prediction_error_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(10))
    delay_probability: Mapped[float] = mapped_column(Float)
    risk_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    input_features: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    shipment = relationship("Shipment", back_populates="predictions")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id", ondelete="CASCADE"), index=True)
    risk_level: Mapped[str] = mapped_column(String(10))
    predicted_delivery_minutes: Mapped[int] = mapped_column(Integer)
    promised_delivery_minutes: Mapped[int] = mapped_column(Integer)
    predicted_eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(Text, default="")
    message: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    shipment = relationship("Shipment", back_populates="alerts")
