from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.models.enums import RiskLevel, ShipmentStatus, TrafficLevel, VehicleType, WeatherCondition


def _ensure_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


UtcDatetime = Annotated[datetime, AfterValidator(_ensure_utc)]


# ---------------- auth ----------------
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str
    user_name: str = ""


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str


# ---------------- shipments ----------------
SHIPMENT_CODE_PATTERN = r"^[A-Za-z][A-Za-z0-9_-]{0,38}$"


class ShipmentBase(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    distance_km: float = Field(gt=0, le=5000)
    traffic_level: TrafficLevel
    weather_condition: WeatherCondition
    vehicle_type: VehicleType
    hour_of_day: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6, description="0 = Monday ... 6 = Sunday")
    warehouse_delay_minutes: int = Field(default=0, ge=0, le=1440)
    previous_route_delay_minutes: int = Field(default=0, ge=0, le=1440)
    promised_delivery_minutes: int = Field(gt=0, le=20000)
    actual_delivery_minutes: Optional[int] = Field(default=None, gt=0, le=40000)
    current_status: ShipmentStatus = ShipmentStatus.PENDING


class ShipmentCreate(ShipmentBase):
    shipment_id: Optional[str] = Field(default=None, pattern=SHIPMENT_CODE_PATTERN, description="Auto-generated if omitted")


class ShipmentUpdate(BaseModel):
    """PUT body. Any field omitted keeps its current value."""
    source: Optional[str] = Field(default=None, min_length=1, max_length=120)
    destination: Optional[str] = Field(default=None, min_length=1, max_length=120)
    distance_km: Optional[float] = Field(default=None, gt=0, le=5000)
    traffic_level: Optional[TrafficLevel] = None
    weather_condition: Optional[WeatherCondition] = None
    vehicle_type: Optional[VehicleType] = None
    hour_of_day: Optional[int] = Field(default=None, ge=0, le=23)
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6)
    warehouse_delay_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    previous_route_delay_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    promised_delivery_minutes: Optional[int] = Field(default=None, gt=0, le=20000)
    actual_delivery_minutes: Optional[int] = Field(default=None, gt=0, le=40000)
    current_status: Optional[ShipmentStatus] = None


class ShipmentOut(ShipmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: str
    created_at: UtcDatetime
    updated_at: UtcDatetime
    predicted_delivery_minutes: Optional[int] = None
    predicted_eta: Optional[UtcDatetime] = None
    risk_level: Optional[RiskLevel] = None
    delay_probability: Optional[float] = None
    risk_reasons: Optional[list[str]] = None


# ---------------- predictions ----------------
class PredictionRequest(BaseModel):
    distance_km: float = Field(gt=0, le=5000)
    traffic_level: TrafficLevel
    weather_condition: WeatherCondition
    vehicle_type: VehicleType
    hour_of_day: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)
    warehouse_delay_minutes: int = Field(default=0, ge=0, le=1440)
    previous_route_delay_minutes: int = Field(default=0, ge=0, le=1440)
    promised_delivery_minutes: int = Field(gt=0, le=20000)
    # optional context
    shipment_id: Optional[str] = Field(default=None, description="Shipment code; if given the result is linked to it")
    source: Optional[str] = None
    destination: Optional[str] = None


class PredictionResult(BaseModel):
    predicted_delivery_minutes: int
    promised_delivery_minutes: int
    predicted_eta: UtcDatetime
    expected_delay_minutes: int
    risk_level: RiskLevel
    delay_probability: float
    risk_reasons: list[str]


class WhatIfOverrides(BaseModel):
    traffic_level: Optional[TrafficLevel] = None
    weather_condition: Optional[WeatherCondition] = None
    vehicle_type: Optional[VehicleType] = None
    warehouse_delay_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    previous_route_delay_minutes: Optional[int] = Field(default=None, ge=0, le=1440)


class WhatIfRequest(BaseModel):
    base: PredictionRequest
    overrides: WhatIfOverrides


class WhatIfResponse(BaseModel):
    original: PredictionResult
    modified: PredictionResult
    difference_minutes: int
    risk_changed: bool
    applied_overrides: dict


class PredictionHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: Optional[int] = None
    shipment_code: Optional[str] = None
    predicted_delivery_minutes: int
    promised_delivery_minutes: int
    actual_delivery_minutes: Optional[int] = None
    prediction_error_minutes: Optional[float] = None
    risk_level: RiskLevel
    delay_probability: float
    risk_reasons: Optional[list[str]] = None
    created_at: UtcDatetime


class ShipmentDetail(ShipmentOut):
    prediction_history: list[PredictionHistoryOut] = []


# ---------------- alerts ----------------
class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: int
    shipment_code: str = ""
    risk_level: RiskLevel
    predicted_delivery_minutes: int
    promised_delivery_minutes: int
    predicted_eta: Optional[UtcDatetime] = None
    expected_delay_minutes: int
    reason: str
    message: str
    is_read: bool
    created_at: UtcDatetime
