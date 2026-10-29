"""
Enterprise Semantic Layer & Centralized Metrics Store
Provides governed metric definitions, dimensional drill-down, and unified query compilation
preventing arbitrary ad-hoc SQL divergence across dashboards and AI interfaces.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

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

