"""
Enterprise Data Lineage DAG Engine
Models end-to-end lineage from ingestion connectors through lakehouse layers (Raw -> Cleaned -> Curated)
down to downstream analytics, ML models, and executive dashboards.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class LineageNode:
    def __init__(
        self,
        id: str,
        name: str,
        layer: str,  # "source", "raw", "clean", "curated", "metric", "model", "dashboard"
        source: str,
        transformation: str,
        last_updated: str,
        records: int,
        quality_score: float,
        upstream: List[str],
        downstream: List[str],
        owner: str = "Data Platform Team"
    ):
        self.id = id
        self.name = name
        self.layer = layer
        self.source = source
        self.transformation = transformation
        self.last_updated = last_updated
        self.records = records
        self.quality_score = quality_score
        self.upstream = upstream
        self.downstream = downstream
        self.owner = owner

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "layer": self.layer,
            "source": self.source,
            "transformation": self.transformation,
            "last_updated": self.last_updated,
            "records": self.records,
            "quality_score": self.quality_score,
            "upstream_datasets": self.upstream,
            "upstream_count": len(self.upstream),
            "downstream_consumers": self.downstream,
            "downstream_count": len(self.downstream),
            "owner": self.owner
        }

class LineageGraph:
    def __init__(self):
        self._nodes: Dict[str, LineageNode] = {}
        self._seed_default_graph()

    def _seed_default_graph(self):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        nodes = [
            LineageNode(
                id="src_pos_sales",
                name="Sales PostgreSQL Production",
                layer="source",
                source="postgresql://pg-prod.internal:5432/enterprise_sales",
                transformation="Direct Ingestion via CDC / Batch Connector",
                last_updated=now_str,
                records=4823921,
                quality_score=98.7,
                upstream=[],
                downstream=["lake_raw_sales"],
                owner="Transactional Database Admin"
            ),
            LineageNode(
                id="lake_raw_sales",
                name="Raw Sales Orders (Bronze)",
                layer="raw",
                source="src_pos_sales",
                transformation="Parquet partitioned stream landing in S3 Bronze zone with raw payload & metadata",
                last_updated=now_str,
                records=4823921,
                quality_score=97.4,
                upstream=["src_pos_sales"],
                downstream=["lake_clean_sales"],
                owner="Data Engineering"
            ),
            LineageNode(
                id="lake_clean_sales",
                name="Cleaned Sales Orders (Silver)",
                layer="clean",
                source="lake_raw_sales",
                transformation="Deduplicated on order_id; PII tokenized; Null revenue filtered; ISO timestamp standardization",
                last_updated=now_str,
                records=4819200,
                quality_score=99.2,
                upstream=["lake_raw_sales"],
                downstream=["lake_curated_sales"],
                owner="Data Quality & Governance"
            ),
            LineageNode(
                id="lake_curated_sales",
                name="Curated Sales Fact Table (Gold)",
                layer="curated",
                source="lake_clean_sales",
                transformation="Enriched with Customer Dim & Exchange Rates; Star Schema optimization",
                last_updated=now_str,
                records=4819200,
                quality_score=99.8,
                upstream=["lake_clean_sales"],
                downstream=["kpi_revenue", "model_forecast_xgb", "model_segmentation_rfm"],
                owner="Analytics Engineering"
            ),
            LineageNode(
                id="kpi_revenue",
                name="Revenue KPI Metric",
                layer="metric",
                source="lake_curated_sales",
                transformation="SUM(order_amount) WHERE status = 'completed' AND currency = 'EUR'",
                last_updated=now_str,
                records=4819200,
                quality_score=100.0,
                upstream=["lake_curated_sales"],
                downstream=["dash_executive"],
                owner="Finance & Corporate BI"
            ),
            LineageNode(
                id="model_forecast_xgb",
                name="Revenue Forecast Model (XGBoost v7)",
                layer="model",
                source="lake_curated_sales",
                transformation="Lagged feature engineering (7d, 30d, 90d), Fourier seasonality, Quantile Loss prediction intervals",
                last_updated=now_str,
                records=4819200,
                quality_score=98.5,
                upstream=["lake_curated_sales"],
                downstream=["dash_executive"],
                owner="Enterprise MLOps Team"
            ),
            LineageNode(
                id="model_segmentation_rfm",
                name="Customer Segmentation Engine",
                layer="model",
                source="lake_curated_sales",
                transformation="Recency, Frequency, Monetary (RFM) K-Means clustering + PCA dimensionality reduction",
                last_updated=now_str,
                records=4819200,
                quality_score=97.9,
                upstream=["lake_curated_sales"],
                downstream=["dash_marketing"],
                owner="Growth & Data Science"
            ),
            LineageNode(
                id="dash_executive",
                name="Executive Business Dashboard",
                layer="dashboard",
                source="kpi_revenue, model_forecast_xgb",
                transformation="Multi-widget reactive synthesis with drift alerts & prescriptive scenarios",
                last_updated=now_str,
                records=4819200,
                quality_score=99.5,
                upstream=["kpi_revenue", "model_forecast_xgb"],
                downstream=[],
                owner="Executive Leadership"
            ),
            LineageNode(
                id="dash_marketing",
                name="Marketing Segmentation Dashboard",
                layer="dashboard",
                source="model_segmentation_rfm",
                transformation="Cohort analysis, retention heatmaps & CLV lifetime projections",
                last_updated=now_str,
                records=4819200,
                quality_score=98.0,
                upstream=["model_segmentation_rfm"],
                downstream=[],
                owner="Marketing Operations"
            )
        ]
        for node in nodes:
            self._nodes[node.id] = node

    def get_lineage_graph(self, dataset_name: Optional[str] = None, row_count: int = 1000, columns: Optional[List[str]] = None, storage_table: Optional[str] = None, quality_score: float = 98.5) -> Dict[str, Any]:
        if not dataset_name or dataset_name == "sales_orders":
            nodes_list = [n.to_dict() for n in self._nodes.values()]
            edges_list = []
            for n in self._nodes.values():
                for target_id in n.downstream:
                    edges_list.append({
                        "from": n.id,
                        "to": target_id
                    })
            return {
                "nodes": nodes_list,
                "edges": edges_list
            }

        # Dynamic Lineage Graph for the active dataset
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        slug = dataset_name.lower().replace(".", "_").replace(" ", "_").replace("-", "_")
        col_list = columns or ["index", "value", "date"]
        col_sample = ", ".join(col_list[:4])
        tbl = storage_table or f"lake_{slug}"

        # Clean display name
        display_title = dataset_name.replace(".csv", "").replace("_", " ").title()

        dynamic_nodes = [
            LineageNode(
                id=f"src_{slug}",
                name=f"{display_title} Source Stream",
                layer="source",
                source=f"s3://enterprise-ingestion/stream/{slug}/raw_feed",
                transformation="Direct Streaming Ingestion via Batch File / CDC Ingestion Adapter",
                last_updated=now_str,
                records=row_count,
                quality_score=round(min(99.5, quality_score), 1),
                upstream=[],
                downstream=[f"lake_raw_{slug}"],
                owner="Data Ingestion Engineering"
            ),
            LineageNode(
                id=f"lake_raw_{slug}",
                name=f"Raw Ingestion Lakehouse (Bronze)",
                layer="raw",
                source=f"src_{slug}",
                transformation="Parquet partitioned stream landing in S3 Bronze zone with raw payload & immutable SHA-256 audit",
                last_updated=now_str,
                records=row_count,
                quality_score=round(max(90.0, quality_score - 1.4), 1),
                upstream=[f"src_{slug}"],
                downstream=[f"lake_clean_{slug}"],
                owner="Data Platform Team"
            ),
            LineageNode(
                id=f"lake_clean_{slug}",
                name=f"Sanitized & Validated Mart (Silver)",
                layer="clean",
                source=f"lake_raw_{slug}",
                transformation=f"Persisted in PostgreSQL table '{tbl}'; 6-dimension quality gates enforced; schema validated; nulls checked",
                last_updated=now_str,
                records=row_count,
                quality_score=round(quality_score, 1),
                upstream=[f"lake_raw_{slug}"],
                downstream=[f"lake_curated_{slug}"],
                owner="Data Quality & Governance"
            ),
            LineageNode(
                id=f"lake_curated_{slug}",
                name=f"Curated Analytic Mart (Gold)",
                layer="curated",
                source=f"lake_clean_{slug}",
                transformation=f"Features engineered: [{col_sample}]; normalized indexes; star-schema dimension linkage",
                last_updated=now_str,
                records=row_count,
                quality_score=round(min(100.0, quality_score + 0.8), 1),
                upstream=[f"lake_clean_{slug}"],
                downstream=[f"metric_{slug}", "model_anomaly_isof", "model_forecast_quantile"],
                owner="Analytics Engineering"
            ),
            LineageNode(
                id=f"metric_{slug}",
                name=f"{display_title} Governed Semantic Metric",
                layer="metric",
                source=f"lake_curated_{slug}",
                transformation=f"Certified SQL aggregation over gold table '{tbl}'",
                last_updated=now_str,
                records=row_count,
                quality_score=100.0,
                upstream=[f"lake_curated_{slug}"],
                downstream=["dash_executive", "dash_market_radar"],
                owner="Corporate FP&A / BI"
            ),
            LineageNode(
                id="model_anomaly_isof",
                name="Multivariate Anomaly Model (Isolation Forest)",
                layer="model",
                source=f"lake_curated_{slug}",
                transformation="Scikit-learn IsolationForest (contamination=0.05, 100 trees) detecting feature deviations",
                last_updated=now_str,
                records=row_count,
                quality_score=98.6,
                upstream=[f"lake_curated_{slug}"],
                downstream=["dash_executive"],
                owner="Enterprise MLOps Team"
            ),
            LineageNode(
                id="model_forecast_quantile",
                name="Chronological Forecast Engine (Quantile Loss)",
                layer="model",
                source=f"lake_curated_{slug}",
                transformation="Multi-horizon temporal forecasting with P10/P50/P90 probabilistic uncertainty bands",
                last_updated=now_str,
                records=row_count,
                quality_score=98.2,
                upstream=[f"lake_curated_{slug}"],
                downstream=["dash_executive", "dash_market_radar"],
                owner="Quantitative Intelligence"
            ),
            LineageNode(
                id="dash_executive",
                name="Executive Decision Cockpit",
                layer="dashboard",
                source=f"metric_{slug}, model_anomaly_isof, model_forecast_quantile",
                transformation="Executive multi-dimensional telemetry, anomaly alerts & trend progression",
                last_updated=now_str,
                records=row_count,
                quality_score=99.8,
                upstream=[f"metric_{slug}", "model_anomaly_isof", "model_forecast_quantile"],
                downstream=[],
                owner="Executive Leadership"
            ),
            LineageNode(
                id="dash_market_radar",
                name="Autonomous Market Radar & Causal AI",
                layer="dashboard",
                source=f"metric_{slug}, model_forecast_quantile",
                transformation="Causal transmission shocks, pass-through elasticity equations, prescriptive supplier mitigations",
                last_updated=now_str,
                records=row_count,
                quality_score=99.5,
                upstream=[f"metric_{slug}", "model_forecast_quantile"],
                downstream=[],
                owner="Risk & Strategy Committee"
            )
        ]

        nodes_list = [n.to_dict() for n in dynamic_nodes]
        edges_list = []
        for n in dynamic_nodes:
            for target_id in n.downstream:
                edges_list.append({
                    "from": n.id,
                    "to": target_id
                })
        return {
            "nodes": nodes_list,
            "edges": edges_list
        }

    def get_node_lineage(self, node_id: str) -> Optional[Dict[str, Any]]:
        node = self._nodes.get(node_id)
        return node.to_dict() if node else None

lineage_engine = LineageGraph()

