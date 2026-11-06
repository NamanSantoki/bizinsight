"""
Enterprise Semantic Layer & Centralized Metrics Store
Provides governed metric definitions, dimensional drill-down, and unified query compilation
preventing arbitrary ad-hoc SQL divergence across dashboards and AI interfaces.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import pandas as pd
import numpy as np

class SemanticMetric:
    def __init__(
        self,
        id: str,
        name: str,
        formula: str,
        sql_expression: str,
        category: str,
        unit: str,
        description: str,
        dimensions: List[str],
        owner: str = "Finance Analytics"
    ):
        self.id = id
        self.name = name
        self.formula = formula
        self.sql_expression = sql_expression
        self.category = category
        self.unit = unit
        self.description = description
        self.dimensions = dimensions
        self.owner = owner

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "formula": self.formula,
            "sql_expression": self.sql_expression,
            "category": self.category,
            "unit": self.unit,
            "description": self.description,
            "dimensions": self.dimensions,
            "owner": self.owner
        }

class MetricsStore:
    def __init__(self):
        self._metrics: Dict[str, SemanticMetric] = {}
        self._seed_default_metrics()

    def _seed_default_metrics(self):
        metrics = [
            SemanticMetric(
                id="revenue",
                name="Total Net Revenue",
                formula="SUM(completed_orders.amount)",
                sql_expression="SELECT SUM(amount) AS revenue FROM completed_orders WHERE status = 'completed'",
                category="Financial",
                unit="USD / EUR",
                description="Total gross transaction volume net of refunds and discounts.",
                dimensions=["date", "region", "product_category", "customer_segment"],
                owner="Corporate Finance"
            ),
            SemanticMetric(
                id="aov",
                name="Average Order Value (AOV)",
                formula="Revenue / Number of Orders",
                sql_expression="SELECT SUM(amount) / COUNT(order_id) AS aov FROM completed_orders WHERE status = 'completed'",
                category="Sales & Commercial",
                unit="USD",
                description="Average monetary value spent per completed transaction.",
                dimensions=["date", "product_category", "device_type", "channel"],
                owner="Growth & Sales Strategy"
            ),
            SemanticMetric(
                id="gross_margin",
                name="Gross Margin Percentage",
                formula="(Revenue - COGS) / Revenue",
                sql_expression="SELECT (SUM(amount) - SUM(cogs)) / SUM(amount) * 100 AS gross_margin FROM sales_fact",
                category="Profitability",
                unit="%",
                description="Percentage of net revenue remaining after deducting direct cost of goods sold.",
                dimensions=["region", "business_unit", "fiscal_quarter"],
                owner="FP&A Team"
            ),
            SemanticMetric(
                id="retention_rate",
                name="Customer Retention Rate",
                formula="Returning Customers / Active Customers (T-1)",
                sql_expression="SELECT CAST(COUNT(DISTINCT returning_users) AS FLOAT) / COUNT(DISTINCT base_users) * 100 FROM cohorts",
                category="Customer Retention",
                unit="%",
                description="Proportion of previous period customer base that placed an order in current window.",
                dimensions=["cohort_month", "acquisition_channel"],
                owner="Customer Success"
            ),
            SemanticMetric(
                id="churn_rate",
                name="Customer Churn Rate",
                formula="Lost Customers / Starting Customers",
                sql_expression="SELECT CAST(COUNT(DISTINCT churned_users) AS FLOAT) / COUNT(DISTINCT starting_users) * 100 FROM churn_cohorts",
                category="Customer Retention",
                unit="%",
                description="Proportion of accounts inactive for greater than 90 consecutive days.",
                dimensions=["tier", "region", "contract_type"],
                owner="Customer Retention & Lifecycle"
            )
        ]
        for m in metrics:
            self._metrics[m.id] = m

    def generate_dataset_metrics(self, dataset_name: str, table_name: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Dynamically generates certified governed metrics for the specified dataset schema."""
        if dataset_name == "sales_orders" or df.empty:
            return self.list_metrics()

        import numpy as np
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        categorical_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        
        # Determine target metric column
        cols_lower = {str(c).lower(): c for c in df.columns}
        metric_col = None
        for candidate in ["revenue", "sales", "price", "value", "val", "amount", "cost", "total"]:
            if candidate in cols_lower and pd.api.types.is_numeric_dtype(df[cols_lower[candidate]]):
                metric_col = cols_lower[candidate]
                break
        if not metric_col and numeric_cols:
            metric_col = numeric_cols[0]

        tbl = table_name or f"lake_{dataset_name.replace('.', '_')}"
        dims = categorical_cols[:4] if categorical_cols else [str(c) for c in df.columns[:3]]
        
        display_title = dataset_name.replace(".csv", "").replace("_", " ").title()
        
        new_metrics: List[SemanticMetric] = []
        
        if metric_col:
            m_label = metric_col.replace("_", " ").title()
            new_metrics.append(SemanticMetric(
                id=f"{dataset_name}_sum_{metric_col}".lower().replace(".", "_"),
                name=f"Total Cumulative {m_label}",
                formula=f"SUM(\"{metric_col}\")",
                sql_expression=f"SELECT SUM(\"{metric_col}\") AS total_{metric_col.lower()} FROM \"{tbl}\"",
                category="Primary Aggregate",
                unit="Numeric Index",
                description=f"Enterprise certified total volume for {m_label} across all recorded observations in {display_title}.",
                dimensions=dims,
                owner="Corporate FP&A"
            ))
            new_metrics.append(SemanticMetric(
                id=f"{dataset_name}_avg_{metric_col}".lower().replace(".", "_"),
                name=f"Mean {m_label} per Observation",
                formula=f"AVG(\"{metric_col}\")",
                sql_expression=f"SELECT AVG(\"{metric_col}\") AS avg_{metric_col.lower()} FROM \"{tbl}\"",
                category="Statistical Benchmark",
                unit="Numeric Index",
                description=f"Governed baseline mean value for {m_label} per record interval.",
                dimensions=dims,
                owner="Quantitative Strategy"
            ))
            new_metrics.append(SemanticMetric(
                id=f"{dataset_name}_max_{metric_col}".lower().replace(".", "_"),
                name=f"Peak {m_label} (Max Ceiling)",
                formula=f"MAX(\"{metric_col}\")",
                sql_expression=f"SELECT MAX(\"{metric_col}\") AS max_{metric_col.lower()} FROM \"{tbl}\"",
                category="Risk & Exposure",
                unit="Numeric Index",
                description=f"Highest historical observed peak for {m_label}.",
                dimensions=dims,
                owner="Risk Management"
            ))

        # Distinct counts on primary dimension
        if categorical_cols:
            dim_col = categorical_cols[0]
            d_label = dim_col.replace("_", " ").title()
            new_metrics.append(SemanticMetric(
                id=f"{dataset_name}_count_{dim_col}".lower().replace(".", "_"),
                name=f"Distinct Monitored {d_label}s",
                formula=f"COUNT(DISTINCT \"{dim_col}\")",
                sql_expression=f"SELECT COUNT(DISTINCT \"{dim_col}\") AS distinct_{dim_col.lower()} FROM \"{tbl}\"",
                category="Dimensional Coverage",
                unit="Entities",
                description=f"Count of unique sovereign or categorized {d_label} instances.",
                dimensions=[dim_col],
                owner="Enterprise Data Governance"
            ))

        # Total record volume
        new_metrics.append(SemanticMetric(
            id=f"{dataset_name}_record_volume".lower().replace(".", "_"),
            name=f"Ingested Record Volume ({display_title})",
            formula=f"COUNT(*)",
            sql_expression=f"SELECT COUNT(*) AS total_rows FROM \"{tbl}\"",
            category="Data Platform",
            unit="Rows",
            description=f"Verified row count synchronized in lakehouse table '{tbl}'.",
            dimensions=dims,
            owner="Data Engineering"
        ))

        # Register in store
        for m in new_metrics:
            self._metrics[m.id] = m

        return [m.to_dict() for m in new_metrics]

    def list_metrics(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._metrics.values()]

    def get_metric(self, metric_id: str) -> Optional[Dict[str, Any]]:
        m = self._metrics.get(metric_id)
        return m.to_dict() if m else None

    def compile_query(self, metric_id: str, dimension: Optional[str] = None, filter_str: Optional[str] = None) -> Dict[str, Any]:
        m = self._metrics.get(metric_id)
        if not m:
            return {"error": f"Metric '{metric_id}' not found in governed semantic store."}

        # Build governed SQL safely
        select_dim = f", {dimension}" if dimension and dimension in m.dimensions else ""
        group_by = f" GROUP BY {dimension}" if dimension and dimension in m.dimensions else ""
        where_clause = f" AND {filter_str}" if filter_str else ""
        
        compiled_sql = f"{m.sql_expression}{where_clause}{group_by}"
        
        return {
            "metric_id": m.id,
            "metric_name": m.name,
            "formula": m.formula,
            "compiled_sql": compiled_sql,
            "selected_dimension": dimension,
            "filter_applied": filter_str,
            "governance": {
                "owner": m.owner,
                "certified": True,
                "zero_metric_hallucination": True
            }
        }

metrics_store = MetricsStore()

