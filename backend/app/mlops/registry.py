"""
Enterprise MLOps Model Registry Engine
Manages model artifacts, lineage, versioning (v1..v7), evaluation metrics (MAE, RMSE, Accuracy),
and governed lifecycle state transitions:
TRAINED -> EVALUATION -> VALIDATION -> PENDING_APPROVAL -> APPROVED -> STAGING -> PRODUCTION
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

class ModelVersion:
    def __init__(
        self,
        model_id: str,
        name: str,
        version: str,
        algorithm: str,
        dataset: str,
        features_count: int,
        training_period: str,
        mae: float,
        rmse: float,
        accuracy_score: float,
        status: str,  # TRAINED, EVALUATION, VALIDATION, PENDING_APPROVAL, APPROVED, STAGING, PRODUCTION
        created_at: str,
        owner: str = "Lead MLOps Engineer"
    ):
        self.model_id = model_id
        self.name = name
        self.version = version
        self.algorithm = algorithm
        self.dataset = dataset
        self.features_count = features_count
        self.training_period = training_period
        self.mae = mae
        self.rmse = rmse
        self.accuracy_score = accuracy_score
        self.status = status
        self.created_at = created_at
        self.owner = owner

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "version": self.version,
            "algorithm": self.algorithm,
            "dataset": self.dataset,
            "features_count": self.features_count,
            "training_period": self.training_period,
            "mae": self.mae,
            "rmse": self.rmse,
            "accuracy_score": self.accuracy_score,
            "status": self.status,
            "created_at": self.created_at,
            "owner": self.owner
        }

class ModelRegistry:
    LIFECYCLE_STATES = [
        "TRAINED",
        "EVALUATION",
        "VALIDATION",
        "PENDING_APPROVAL",
        "APPROVED",
        "STAGING",
        "PRODUCTION"
    ]

    def __init__(self):
        self._models: Dict[str, List[ModelVersion]] = {}
        self._seed_default_registry()

    def _seed_default_registry(self):
        # Revenue Forecast Model versions
        v_list = [
            ModelVersion("rev_fc_01", "Revenue Forecast Model", "v1", "ARIMA", "sales_raw_v1", 4, "2020-2021", 28400, 39100, 78.4, "ARCHIVED", "2024-01-10"),
            ModelVersion("rev_fc_02", "Revenue Forecast Model", "v2", "Prophet", "sales_clean_v3", 6, "2020-2022", 21200, 29800, 83.1, "ARCHIVED", "2024-06-15"),
            ModelVersion("rev_fc_03", "Revenue Forecast Model", "v3", "RandomForest", "sales_curated_v5", 10, "2021-2023", 18900, 26400, 86.8, "ARCHIVED", "2025-01-20"),
            ModelVersion("rev_fc_04", "Revenue Forecast Model", "v4", "LightGBM", "sales_curated_v8", 14, "2021-2024", 16400, 23100, 89.5, "ARCHIVED", "2025-07-12"),
            ModelVersion("rev_fc_05", "Revenue Forecast Model", "v5", "XGBoost", "sales_curated_v10", 16, "2022-2024", 14200, 21000, 91.8, "ARCHIVED", "2026-01-18"),
            ModelVersion("rev_fc_06", "Revenue Forecast Model", "v6", "XGBoost Quantile", "sales_curated_v11", 17, "2022-2025", 13100, 19800, 93.4, "STAGING", "2026-07-22"),
            ModelVersion("rev_fc_07", "Revenue Forecast Model", "v7", "XGBoost Enterprise", "sales_curated_v12", 17, "2022-2025", 12482, 19201, 94.2, "PRODUCTION", "2026-10-29"),
        ]
        self._models["Revenue Forecast Model"] = v_list

        # Churn Prediction Model
        churn_list = [
            ModelVersion("churn_01", "Customer Churn Classifier", "v1", "LogisticRegression", "crm_customers_v1", 8, "2023-2024", 0.28, 0.34, 82.1, "ARCHIVED", "2025-03-10"),
            ModelVersion("churn_02", "Customer Churn Classifier", "v2", "CatBoost", "crm_customers_v3", 12, "2024-2025", 0.16, 0.22, 91.5, "PRODUCTION", "2026-09-14")
        ]
        self._models["Customer Churn Classifier"] = churn_list

    def list_models(self) -> List[Dict[str, Any]]:
        results = []
        for name, versions in self._models.items():
            prod_ver = next((v for v in versions if v.status == "PRODUCTION"), versions[-1])
            results.append({
                "name": name,
                "current_production_version": prod_ver.version,
                "latest_version": versions[-1].version,
                "algorithm": prod_ver.algorithm,
                "total_versions": len(versions),
                "production_details": prod_ver.to_dict(),
                "versions": [v.to_dict() for v in versions]
            })
        return results

    def get_model(self, name: str) -> Optional[Dict[str, Any]]:
        versions = self._models.get(name)
        if not versions:
            return None
        return {
            "name": name,
            "versions": [v.to_dict() for v in versions]
        }

    def transition_stage(self, model_name: str, version: str, target_stage: str, reviewer: str = "admin") -> Dict[str, Any]:
        if target_stage not in self.LIFECYCLE_STATES:
            return {"error": f"Invalid stage '{target_stage}'. Must be one of {self.LIFECYCLE_STATES}"}

        versions = self._models.get(model_name)
        if not versions:
            return {"error": f"Model '{model_name}' not found."}

        target_v = next((v for v in versions if v.version == version), None)
        if not target_v:
            return {"error": f"Version '{version}' not found for model '{model_name}'."}

        # If promoting to production, archive old production version
        if target_stage == "PRODUCTION":
            for v in versions:
                if v.status == "PRODUCTION":
                    v.status = "ARCHIVED"

        previous_stage = target_v.status
        target_v.status = target_stage

        return {
            "model_name": model_name,
            "version": version,
            "previous_stage": previous_stage,
            "new_stage": target_stage,
            "updated_by": reviewer,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "status": "success"
        }

model_registry = ModelRegistry()

