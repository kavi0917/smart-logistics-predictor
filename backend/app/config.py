"""Central configuration. All values can be overridden with environment variables (.env)."""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> project root is two levels above "app"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), ".env"), extra="ignore", protected_namespaces=()
    )

    # --- infrastructure ---
    database_url: str = "sqlite:///./logistics_dev.db"  # Docker/.env.example switch this to PostgreSQL
    secret_key: str = "dev-only-secret-change-me"  # override with SECRET_KEY in .env
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    model_path: str = "models/eta_model.joblib"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    seed_on_startup: bool = True

    # --- local demo account (documented demo credentials, NOT for production) ---
    demo_user_email: str = "admin@logistics.local"
    demo_user_password: str = "Admin@123"
    demo_user_name: str = "Demo Admin"

    # --- risk classification thresholds (ratio = predicted / promised) ---
    risk_medium_ratio: float = 1.00  # above this -> at least MEDIUM
    risk_high_ratio: float = 1.15    # above this -> HIGH
    probability_scale_ratio: float = 0.08  # steepness of the delay-probability curve
    probability_min_scale_minutes: float = 10.0

    # --- thresholds used for human-readable risk reasons ---
    long_distance_km: float = 300
    warehouse_delay_threshold: int = 20
    previous_delay_threshold: int = 15
    peak_hours: str = "8,9,10,17,18,19,20"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def peak_hour_list(self) -> List[int]:
        return [int(h) for h in self.peak_hours.split(",") if h.strip()]

    @property
    def resolved_model_path(self) -> Path:
        p = Path(self.model_path)
        return p if p.is_absolute() else PROJECT_ROOT / p


@lru_cache
def get_settings() -> Settings:
    return Settings()
