from fastapi import APIRouter, Depends

from app.config import get_settings
from app.ml.predictor import predictor
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/settings", tags=["Settings"], dependencies=[Depends(get_current_user)])


@router.get("")
def read_settings():
    """Read-only view of the active risk thresholds and model information."""
    s = get_settings()
    return {
        "risk_thresholds": {
            "medium_if_predicted_over_promised_ratio": s.risk_medium_ratio,
            "high_if_predicted_over_promised_ratio": s.risk_high_ratio,
            "probability_scale_ratio": s.probability_scale_ratio,
        },
        "reason_thresholds": {
            "long_distance_km": s.long_distance_km,
            "warehouse_delay_minutes": s.warehouse_delay_threshold,
            "previous_route_delay_minutes": s.previous_delay_threshold,
            "peak_hours": s.peak_hour_list,
        },
        "model": {
            "path": str(s.model_path),
            "file_exists": predictor.path.exists(),
            "metrics": predictor.metrics(),
        },
        "note": "Delay probability is a heuristic risk score, not a statistically calibrated probability.",
    }
