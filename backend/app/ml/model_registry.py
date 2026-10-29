import os
import joblib
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

# Base directory for model artifacts – placed under project root /ml/models
BASE_MODEL_DIR = Path(__file__).resolve().parents[1] / "models"

def _model_dir(model_name: str) -> Path:
    """Return the directory for a given model name, creating it if necessary."""
    path = BASE_MODEL_DIR / model_name
    path.mkdir(parents=True, exist_ok=True)
    return path

def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d%H%M%S")

def save_model(model_name: str, model_obj: Any, metadata: Optional[dict] = None) -> Path:
    """Save a model object to a versioned sub‑directory.

    Args:
        model_name: Logical name of the model (e.g. "xgboost_sales").
        model_obj: Any Python object serialisable by joblib (e.g., sklearn/XGBoost model).
        metadata: Optional dictionary of metadata to store alongside the model.

    Returns:
        Path to the saved ``model.pkl`` file.
    """
    version_dir = _model_dir(model_name) / _timestamp()
    version_dir.mkdir(parents=True, exist_ok=True)
    model_path = version_dir / "model.pkl"
    joblib.dump(model_obj, model_path)
    if metadata:
        joblib.dump(metadata, version_dir / "metadata.pkl")
    return model_path

def load_latest_model(model_name: str) -> Any:
    """Load the most recent model for *model_name*.
    Raises FileNotFoundError if no model exists.
    """
    model_root = _model_dir(model_name)
    if not model_root.exists():
        raise FileNotFoundError(f"No models found for {model_name}")
    # Sort sub‑folders by name (timestamp) descending
    versions = sorted([p for p in model_root.iterdir() if p.is_dir()], reverse=True)
    if not versions:
        raise FileNotFoundError(f"No versioned models under {model_root}")
    latest = versions[0] / "model.pkl"
    return joblib.load(latest)

def list_model_versions(model_name: str) -> List[str]:
    """Return a list of version directory names (timestamps) for *model_name* ordered newest first."""
    model_root = _model_dir(model_name)
    if not model_root.exists():
        return []
    versions = sorted([p.name for p in model_root.iterdir() if p.is_dir()], reverse=True)
    return versions
