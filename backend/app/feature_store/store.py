"""
Enterprise Feature Store Engine (Online & Offline Architecture)
Centralized repository for engineered, reusable ML features with versioning,
provenance lineage, statistical profiling, low-latency online serving, and batch offline generation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class FeatureDefinition:
    def __init__(
        self,
        feature_name: str,
        version: int,
        entity_key: str,
        dtype: str,
        owner: str,
        description: str,
        source_table: str,
        transformation_sql: str,
        freshness_minutes: int,
        statistics: Dict[str, Any],
        downstream_models: List[str]
    ):
        self.feature_name = feature_name
        self.version = version
        self.entity_key = entity_key
        self.dtype = dtype
        self.owner = owner
        self.description = description
        self.source_table = source_table
        self.transformation_sql = transformation_sql
        self.freshness_minutes = freshness_minutes
        self.statistics = statistics
        self.downstream_models = downstream_models

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_name": self.feature_name,
            "version": self.version,
            "entity_key": self.entity_key,
            "dtype": self.dtype,
            "owner": self.owner,
            "description": self.description,
            "source_table": self.source_table,
            "transformation_sql": self.transformation_sql,
            "freshness_minutes": self.freshness_minutes,
            "statistics": self.statistics,
            "downstream_models": self.downstream_models
        }

class EnterpriseFeatureStore:
    def __init__(self):
        self._features: Dict[str, FeatureDefinition] = {}
        self._online_store: Dict[str, Dict[str, Any]] = {}
        self._seed_features()

    def _seed_features(self):
        feat1 = FeatureDefinition(
            feature_name="customer_purchase_frequency",
            version=7,
            entity_key="customer_id",
            dtype="float64",
            owner="Data Science - Growth",
            description="Normalized order count divided by account active months.",
            source_table="gold.customer_orders",
            transformation_sql="COUNT(order_id)::float / GREATEST(active_months, 1)",
            freshness_minutes=12,
            statistics={"min": 0.0, "max": 24.5, "mean": 3.82, "null_pct": 0.0},
            downstream_models=["Customer Churn Model v14", "CLV Prediction Model v8", "Revenue Forecast v7"]
        )
        feat2 = FeatureDefinition(
            feature_name="customer_avg_order_value_90d",
            version=4,
            entity_key="customer_id",
            dtype="float64",
            owner="Commercial Analytics",
            description="Rolling 90-day mean transaction monetary value in EUR.",
            source_table="gold.sales_fact",
            transformation_sql="AVG(amount) FILTER (WHERE order_date >= NOW() - INTERVAL '90 days')",
            freshness_minutes=15,
            statistics={"min": 14.5, "max": 1820.0, "mean": 142.6, "null_pct": 0.0},
            downstream_models=["Revenue Forecast v7", "Discount Propensity v3"]
        )
        feat3 = FeatureDefinition(
            feature_name="customer_recency_days",
            version=5,
            entity_key="customer_id",
            dtype="int64",
            owner="Lifecycle Marketing",
            description="Days elapsed since the most recent successful order confirmation.",
            source_table="gold.customer_dim",
            transformation_sql="DATE_PART('day', NOW() - last_order_timestamp)",
            freshness_minutes=6,
            statistics={"min": 0, "max": 420, "mean": 28.4, "null_pct": 0.0},
            downstream_models=["Customer Churn Model v14", "Re-engagement Trigger v2"]
        )
        feat4 = FeatureDefinition(
            feature_name="marketing_elasticity_ratio",
            version=3,
            entity_key="region_category_key",
            dtype="float64",
            owner="FP&A Strategy",
            description="Econometric ratio of incremental sales lift over marketing dollar outlay.",
            source_table="curated.marketing_attribution",
            transformation_sql="LN(sales_t / sales_t_minus_1) / LN(spend_t / spend_t_minus_1)",
            freshness_minutes=60,
            statistics={"min": -0.2, "max": 1.45, "mean": 0.42, "null_pct": 0.0},
            downstream_models=["Digital Twin Scenario Engine", "Revenue Forecast v7"]
        )

        for f in [feat1, feat2, feat3, feat4]:
            self._features[f.feature_name] = f

        # Seed low-latency online entity records
        self._online_store["cust_1001"] = {
            "customer_id": "cust_1001",
            "customer_purchase_frequency": 5.4,
            "customer_avg_order_value_90d": 218.40,
            "customer_recency_days": 4,
            "last_synced": datetime.now(timezone.utc).isoformat()
        }
        self._online_store["cust_1002"] = {
            "customer_id": "cust_1002",
            "customer_purchase_frequency": 1.2,
            "customer_avg_order_value_90d": 84.10,
            "customer_recency_days": 68,
            "last_synced": datetime.now(timezone.utc).isoformat()
        }

    def list_features(self) -> List[Dict[str, Any]]:
        return [f.to_dict() for f in self._features.values()]

    def get_feature(self, feature_name: str) -> Optional[Dict[str, Any]]:
        f = self._features.get(feature_name)
        return f.to_dict() if f else None

    def get_online_features(self, entity_id: str) -> Dict[str, Any]:
        """Low-latency key-value serving for online inference engines (<10ms)."""
        record = self._online_store.get(entity_id)
        if not record:
            return {
                "entity_id": entity_id,
                "found": False,
                "features": {
                    "customer_purchase_frequency": 3.82,
                    "customer_avg_order_value_90d": 142.60,
                    "customer_recency_days": 28
                },
                "serving_layer": "Online Feature Cache (Redis / In-Memory)"
            }
        return {
            "entity_id": entity_id,
            "found": True,
            "features": record,
            "serving_layer": "Online Feature Cache (Redis / In-Memory)"
        }

# Global Feature Store Singleton
feature_store = EnterpriseFeatureStore()

