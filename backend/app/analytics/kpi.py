import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

def compute_business_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes business KPIs dynamically based on available columns without hard-coding assumptions:
    - Identifies target metrics (revenue, sales, price, amount, quantity, cost, profit)
    - Identifies dimensions (customer, region, product, category, employee)
    - Identifies date/temporal column for trends
    Returns computed KPIs and breakdowns, or graceful honesty if metrics are absent.
    """
    cols_lower = {str(c).lower(): c for c in df.columns}
    
    # 1. Identify Target Numeric Metric (Revenue/Sales/Amount)
    metric_col = None
    for candidate in ["revenue", "sales", "total_amount", "amount", "order_total", "total", "price"]:
        if candidate in cols_lower and pd.api.types.is_numeric_dtype(df[cols_lower[candidate]]):
            metric_col = cols_lower[candidate]
            break

    # Quantity metric
    qty_col = None
    for candidate in ["quantity", "qty", "units", "count"]:
        if candidate in cols_lower and pd.api.types.is_numeric_dtype(df[cols_lower[candidate]]):
            qty_col = cols_lower[candidate]
            break

    # Date metric
    date_col = None
    for candidate in ["date", "order_date", "transaction_date", "invoice_date", "timestamp", "created_at"]:
        if candidate in cols_lower:
            date_col = cols_lower[candidate]
            break

    # Dimension candidates
    customer_col = next((cols_lower[c] for c in ["customer_id", "customer", "customer_name", "client_id"] if c in cols_lower), None)
    product_col = next((cols_lower[c] for c in ["product_id", "product", "product_name", "item", "sku"] if c in cols_lower), None)
    region_col = next((cols_lower[c] for c in ["region", "country", "state", "city", "location", "territory"] if c in cols_lower), None)
    category_col = next((cols_lower[c] for c in ["category", "department", "segment", "type"] if c in cols_lower), None)

    kpis: Dict[str, Any] = {
        "dataset_rows": len(df),
        "available_columns": list(df.columns),
        "primary_metric": metric_col,
        "quantity_metric": qty_col,
        "date_metric": date_col,
        "cards": {}
    }

    # High-level summary cards
    if metric_col:
        total_val = float(df[metric_col].sum())
        avg_val = float(df[metric_col].mean())
        kpis["cards"]["total_metric"] = {
            "label": f"Total {metric_col.replace('_', ' ').title()}",
            "value": round(total_val, 2),
            "formatted": f"{total_val:,.2f}"
        }
        kpis["cards"]["average_metric"] = {
            "label": f"Average {metric_col.replace('_', ' ').title()} per record",
            "value": round(avg_val, 2),
            "formatted": f"{avg_val:,.2f}"
        }
    else:
        kpis["cards"]["records"] = {
            "label": "Total Records",
            "value": len(df),
            "formatted": f"{len(df):,}"
        }

    if qty_col:
        total_qty = float(df[qty_col].sum())
        kpis["cards"]["total_quantity"] = {
            "label": f"Total {qty_col.replace('_', ' ').title()}",
            "value": round(total_qty, 2),
            "formatted": f"{total_qty:,.0f}"
        }

    if customer_col:
        uniq_cust = int(df[customer_col].nunique(dropna=True))
        kpis["cards"]["unique_customers"] = {
            "label": "Distinct Customers",
            "value": uniq_cust,
            "formatted": f"{uniq_cust:,}"
        }

    # Temporal Trend Breakdown (Daily / Monthly)
    trends = []
    if date_col and metric_col:
        try:
            temp_df = df[[date_col, metric_col]].copy()
            temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce')
            temp_df = temp_df.dropna(subset=[date_col])
            
            if len(temp_df) > 0:
                # Group by Month or Day depending on date span
                span_days = (temp_df[date_col].max() - temp_df[date_col].min()).days
                freq = "M" if span_days > 120 else "D"
                grouped = temp_df.groupby(pd.Grouper(key=date_col, freq=freq))[metric_col].agg(['sum', 'count']).reset_index()
                grouped = grouped.sort_values(by=date_col)
                
                for _, r in grouped.iterrows():
                    trends.append({
                        "period": r[date_col].strftime("%Y-%m-%d" if freq == "D" else "%Y-%m"),
                        "value": round(float(r['sum']), 2),
                        "count": int(r['count'])
                    })
        except Exception:
            trends = []
    kpis["trends"] = trends

    # Top Dimension Breakdowns
    breakdowns = {}
    dimension_map = {
        "products": product_col,
        "regions": region_col,
        "categories": category_col
    }

    for dim_name, col_name in dimension_map.items():
        if col_name and metric_col:
            top_df = df.groupby(col_name)[metric_col].sum().reset_index()
            top_df = top_df.sort_values(by=metric_col, ascending=False).head(10)
            breakdowns[dim_name] = [
                {"name": str(r[col_name]), "value": round(float(r[metric_col]), 2)}
                for _, r in top_df.iterrows()
            ]
        elif col_name:
            top_df = df[col_name].value_counts().head(10).reset_index()
            top_df.columns = [col_name, "count"]
            breakdowns[dim_name] = [
                {"name": str(r[col_name]), "value": int(r["count"])}
                for _, r in top_df.iterrows()
            ]

    kpis["breakdowns"] = breakdowns
    return kpis
