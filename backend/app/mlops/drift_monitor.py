from typing import Tuple, Dict, Any
from .monitoring import ml_monitoring

def detect_drift(model_name: str, version: int | str) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect data and prediction drift for a model version.
    Returns (drift_detected: bool, details: dict).
    """
    v_str = f"v{version}" if isinstance(version, int) else str(version)
    for model_id, data in ml_monitoring._monitoring_data.items():
        if model_name.lower() in data.get("model_name", "").lower() or model_id.lower() == model_name.lower():
            is_drifting = data.get("drift_status") in ["WARNING", "CRITICAL"]
            return is_drifting, data
    # Fallback to model telemetry probe
    health = ml_monitoring.get_model_health(f"{model_name}_{v_str}")
    return False, health

