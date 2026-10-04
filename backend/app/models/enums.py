import enum


class ShipmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class TrafficLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WeatherCondition(str, enum.Enum):
    CLEAR = "CLEAR"
    CLOUDY = "CLOUDY"
    RAIN = "RAIN"
    STORM = "STORM"


class VehicleType(str, enum.Enum):
    VAN = "VAN"
    TRUCK = "TRUCK"
    BIKE = "BIKE"
    TEMPO = "TEMPO"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
