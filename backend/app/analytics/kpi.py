import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


def format_compact_metric(val: float) -> str:
    """Formats large numeric values into human-readable compact representations."""
    if abs(val) >= 1e12:
        return f"{val / 1e12:,.2f}T"
    if abs(val) >= 1e9:
        return f"{val / 1e9:,.2f}B"
    if abs(val) >= 1e6:
        return f"{val / 1e6:,.2f}M"
    if abs(val) >= 1e3:
        return f"{val / 1e3:,.2f}K"
    return f"{val:,.2f}"


def compute_business_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes business KPIs dynamically based on available columns without hard-coding assumptions:
    - Identifies target metrics (revenue, sales, price, amount, quantity, cost, profit, value, etc.)
    - Identifies dimensions (customer, region, product, category, employee, country, etc.)
    - Identifies date/temporal column for trends (datetime, dates, or chronological integer years)
    - Computes statistical summaries, distribution histograms, and Pareto concentration.
    Returns comprehensive, executive-ready KPIs and exploratory dimensions.
    """
    if df.empty:
        return {
            "dataset_rows": 0,
            "available_columns": list(df.columns),
            "primary_metric": None,
            "quantity_metric": None,
            "date_metric": None,
            "cards": {
                "records": {"label": "Total Records", "value": 0, "formatted": "0", "compact": "0"}
            },
            "trends": [],
            "breakdowns": {"products": [], "regions": [], "categories": []},
            "distribution": [],
            "summary_stats": {},
            "column_metadata": [],
            "sample_records": []
        }

    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    categorical_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]

    # 1. Identify Target Numeric Metric (Revenue/Sales/Amount/Value/Price)
    metric_col = None
    priority_candidates = [
        "revenue", "sales", "total_amount", "amount", "order_total", "total", "price",
        "value", "val", "gdp", "volume", "cost", "profit", "margin", "expense",
        "score", "rate", "index", "balance", "close", "adj_close", "market_cap"
    ]
    for candidate in priority_candidates:
        if candidate in cols_lower and pd.api.types.is_numeric_dtype(df[cols_lower[candidate]]):
            metric_col = cols_lower[candidate]
            break

    # If no candidate matched, select first non-ID numeric column
    if not metric_col and numeric_cols:
        non_id_numerics = [
            c for c in numeric_cols 
            if not any(c.lower().endswith(suffix) for suffix in ["_id", "id", "key", "index", "code"])
        ]
        metric_col = non_id_numerics[0] if non_id_numerics else numeric_cols[0]

    # 2. Quantity metric
    qty_col = None
    for candidate in ["quantity", "qty", "units", "count", "items"]:
        if candidate in cols_lower and pd.api.types.is_numeric_dtype(df[cols_lower[candidate]]):
            if cols_lower[candidate] != metric_col:
                qty_col = cols_lower[candidate]
                break

    # 3. Date / Temporal metric
    date_col = None
    for candidate in [
        "date", "order_date", "transaction_date", "invoice_date", "timestamp", "created_at",
        "year", "yr", "period", "time", "datetime", "month", "day", "trans_date"
    ]:
        if candidate in cols_lower:
            date_col = cols_lower[candidate]
            break

    # Check for partial matches or datetime types if still not found
    if not date_col:
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                date_col = c
                break
            c_low = c.lower()
            if any(term in c_low for term in ["date", "time", "year"]):
                date_col = c
                break

    # 4. Dimension candidates
    customer_col = next((cols_lower[c] for c in ["customer_id", "customer", "customer_name", "client_id"] if c in cols_lower), None)
    product_col = next((cols_lower[c] for c in ["product_id", "product", "product_name", "item", "sku", "ticker", "symbol"] if c in cols_lower), None)
    
    # Region / Country
    region_col = None
    for cand in ["region", "country", "country name", "state", "city", "location", "territory", "geography", "zone"]:
        if cand in cols_lower:
            region_col = cols_lower[cand]
            break
    if not region_col:
        for c in df.columns:
            if any(term in c.lower() for term in ["country", "region", "state", "city", "location"]):
                region_col = c
                break

    # Category / Sector
    category_col = None
    for cand in ["category", "department", "segment", "type", "sector", "industry", "class", "country code"]:
        if cand in cols_lower and cols_lower[cand] != region_col:
            category_col = cols_lower[cand]
            break
    if not category_col:
        for c in df.columns:
            if c != region_col and any(term in c.lower() for term in ["category", "segment", "type", "sector", "code"]):
                category_col = c
                break

    # Categorical fallbacks if still none found
    usable_categoricals = [
        c for c in categorical_cols 
        if c != date_col and c not in [region_col, category_col, customer_col, product_col] and 2 <= df[c].nunique() <= 150
    ]
    if not region_col and usable_categoricals:
        region_col = usable_categoricals.pop(0)
    if not category_col and usable_categoricals:
        category_col = usable_categoricals.pop(0)

    # Base payload structure
    kpis: Dict[str, Any] = {
        "dataset_rows": len(df),
        "available_columns": list(df.columns),
        "primary_metric": metric_col,
        "quantity_metric": qty_col,
        "date_metric": date_col,
        "cards": {}
    }

    # 5. High-Level Executive Summary Cards
    if metric_col:
        valid_metric = df[metric_col].dropna()
        total_val = float(valid_metric.sum()) if len(valid_metric) > 0 else 0.0
        avg_val = float(valid_metric.mean()) if len(valid_metric) > 0 else 0.0
        max_val = float(valid_metric.max()) if len(valid_metric) > 0 else 0.0
        min_val = float(valid_metric.min()) if len(valid_metric) > 0 else 0.0

        title_label = metric_col.replace("_", " ").title()
        kpis["cards"]["total_metric"] = {
            "label": f"Total {title_label}",
            "value": round(total_val, 2),
            "formatted": f"{total_val:,.2f}",
            "compact": format_compact_metric(total_val),
            "subtitle": "Aggregate across records"
        }
        kpis["cards"]["average_metric"] = {
            "label": f"Average {title_label}",
            "value": round(avg_val, 2),
            "formatted": f"{avg_val:,.2f}",
            "compact": format_compact_metric(avg_val),
            "subtitle": "Mean benchmark per observation"
        }
        kpis["cards"]["peak_metric"] = {
            "label": f"Peak {title_label}",
            "value": round(max_val, 2),
            "formatted": f"{max_val:,.2f}",
            "compact": format_compact_metric(max_val),
            "subtitle": f"Min: {format_compact_metric(min_val)}"
        }
    else:
        kpis["cards"]["records"] = {
            "label": "Total Records",
            "value": len(df),
            "formatted": f"{len(df):,}",
            "compact": f"{len(df):,}",
            "subtitle": "Total verified rows"
        }

    if qty_col:
        valid_qty = df[qty_col].dropna()
        total_qty = float(valid_qty.sum()) if len(valid_qty) > 0 else 0.0
        kpis["cards"]["total_quantity"] = {
            "label": f"Total {qty_col.replace('_', ' ').title()}",
            "value": round(total_qty, 2),
            "formatted": f"{total_qty:,.0f}",
            "compact": format_compact_metric(total_qty),
            "subtitle": "Cumulative unit volume"
        }

    if customer_col:
        uniq_cust = int(df[customer_col].nunique(dropna=True))
        kpis["cards"]["unique_customers"] = {
            "label": "Distinct Entities",
            "value": uniq_cust,
            "formatted": f"{uniq_cust:,}",
            "compact": f"{uniq_cust:,}",
            "subtitle": "Unique customer accounts"
        }
    elif region_col:
        uniq_regions = int(df[region_col].nunique(dropna=True))
        kpis["cards"]["unique_regions"] = {
            "label": f"Monitored {region_col.replace('_', ' ').title()}",
            "value": uniq_regions,
            "formatted": f"{uniq_regions:,}",
            "compact": f"{uniq_regions:,}",
            "subtitle": f"Unique {region_col} boundaries"
        }

    # 6. Temporal Trend Breakdown
    trends: List[Dict[str, Any]] = []
    if date_col and metric_col:
        try:
            temp_df = df[[date_col, metric_col]].dropna().copy()
            if len(temp_df) > 0:
                # Case A: Integer Year column (e.g. 2000, 2001, ...)
                if pd.api.types.is_integer_dtype(temp_df[date_col]) and 1800 <= temp_df[date_col].min() <= 2100:
                    grouped = temp_df.groupby(date_col)[metric_col].agg(['sum', 'count', 'mean']).reset_index()
                    grouped = grouped.sort_values(by=date_col)
                    if len(grouped) > 80:
                        step = max(1, len(grouped) // 50)
                        grouped = grouped.iloc[::step]
                    for _, r in grouped.iterrows():
                        trends.append({
                            "period": str(int(r[date_col])),
                            "value": round(float(r['sum']), 2),
                            "count": int(r['count']),
                            "mean": round(float(r['mean']), 2)
                        })
                else:
                    # Case B: Standard Date / Timestamp string or datetime
                    temp_df[date_col] = pd.to_datetime(temp_df[date_col].astype(str), errors='coerce')
                    temp_df = temp_df.dropna(subset=[date_col])
                    if len(temp_df) > 0:
                        span_days = (temp_df[date_col].max() - temp_df[date_col].min()).days
                        if span_days > 730:
                            freq = "Y"
                            fmt = "%Y"
                        elif span_days > 120:
                            freq = "M"
                            fmt = "%Y-%m"
                        else:
                            freq = "D"
                            fmt = "%Y-%m-%d"
                        
                        grouped = temp_df.groupby(pd.Grouper(key=date_col, freq=freq))[metric_col].agg(['sum', 'count', 'mean']).reset_index()
                        grouped = grouped.dropna(subset=[date_col]).sort_values(by=date_col)
                        
                        if len(grouped) > 80:
                            step = max(1, len(grouped) // 50)
                            grouped = grouped.iloc[::step]

                        for _, r in grouped.iterrows():
                            trends.append({
                                "period": r[date_col].strftime(fmt),
                                "value": round(float(r['sum']), 2),
                                "count": int(r['count']),
                                "mean": round(float(r['mean']), 2)
                            })
        except Exception:
            trends = []
    
    # Fallback trend progression if no date column exists but metric exists (indexed slices)
    if not trends and metric_col and len(df) > 10:
        chunk_size = max(1, len(df) // 30)
        chunks = [df[metric_col].iloc[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
        for idx, chunk in enumerate(chunks[:30]):
            valid_c = chunk.dropna()
            if len(valid_c) > 0:
                trends.append({
                    "period": f"Batch {idx+1}",
                    "value": round(float(valid_c.sum()), 2),
                    "count": len(valid_c),
                    "mean": round(float(valid_c.mean()), 2)
                })

    kpis["trends"] = trends

    # 7. Dimension Breakdowns
    breakdowns: Dict[str, List[Dict[str, Any]]] = {}
    dimension_map = {
        "products": product_col,
        "regions": region_col,
        "categories": category_col
    }

    total_metric_sum = float(df[metric_col].sum()) if metric_col and len(df[metric_col].dropna()) > 0 else 0.0

    for dim_name, col_name in dimension_map.items():
        if col_name and metric_col:
            top_df = df.groupby(col_name)[metric_col].sum().reset_index()
            top_df = top_df.sort_values(by=metric_col, ascending=False).head(10)
            breakdowns[dim_name] = [
                {
                    "name": str(r[col_name]),
                    "value": round(float(r[metric_col]), 2),
                    "share_pct": round(float(r[metric_col]) / total_metric_sum * 100, 1) if total_metric_sum > 0 else 0.0
                }
                for _, r in top_df.iterrows()
            ]
        elif col_name:
            top_df = df[col_name].value_counts().head(10).reset_index()
            top_df.columns = [col_name, "count"]
            total_records = len(df)
            breakdowns[dim_name] = [
                {
                    "name": str(r[col_name]),
                    "value": int(r["count"]),
                    "share_pct": round(int(r["count"]) / total_records * 100, 1) if total_records > 0 else 0.0
                }
                for _, r in top_df.iterrows()
            ]
        else:
            breakdowns[dim_name] = []

    kpis["breakdowns"] = breakdowns

    # 8. Distribution Bins (Histogram for Primary Metric)
    distribution: List[Dict[str, Any]] = []
    if metric_col:
        valid_vals = df[metric_col].dropna().values
        if len(valid_vals) >= 5:
            counts, bin_edges = np.histogram(valid_vals, bins=min(10, len(np.unique(valid_vals))))
            total_items = len(valid_vals)
            for i in range(len(counts)):
                distribution.append({
                    "bin": f"{format_compact_metric(bin_edges[i])} - {format_compact_metric(bin_edges[i+1])}",
                    "count": int(counts[i]),
                    "pct": round(float(counts[i]) / total_items * 100, 1) if total_items > 0 else 0.0
                })
    kpis["distribution"] = distribution

    # 9. Comprehensive Column Metadata & Descriptive Statistics
    column_metadata: List[Dict[str, Any]] = []
    summary_stats: Dict[str, Any] = {}

    for c in df.columns:
        null_count = int(df[c].isna().sum())
        total_len = len(df)
        missing_pct = round((null_count / total_len) * 100, 2) if total_len > 0 else 0.0
        uniq_count = int(df[c].nunique(dropna=True))
        
        # Determine semantic type
        if pd.api.types.is_numeric_dtype(df[c]):
            semantic_type = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[c]) or c == date_col:
            semantic_type = "temporal"
        elif uniq_count < 100:
            semantic_type = "categorical"
        else:
            semantic_type = "text"

        column_metadata.append({
            "name": str(c),
            "dtype": str(df[c].dtype),
            "semantic_type": semantic_type,
            "unique_count": uniq_count,
            "missing_count": null_count,
            "missing_pct": missing_pct
        })

        # Calculate statistics for numeric columns (up to 12)
        if pd.api.types.is_numeric_dtype(df[c]) and len(summary_stats) < 12:
            s = df[c].dropna()
            if len(s) > 0:
                mean_v = float(s.mean())
                total_v = float(s.sum())
                summary_stats[c] = {
                    "mean": round(mean_v, 2),
                    "std": round(float(s.std()), 2) if len(s) > 1 else 0.0,
                    "min": round(float(s.min()), 2),
                    "q25": round(float(s.quantile(0.25)), 2),
                    "median": round(float(s.median()), 2),
                    "q75": round(float(s.quantile(0.75)), 2),
                    "max": round(float(s.max()), 2),
                    "sum": round(total_v, 2),
                    "missing_pct": missing_pct,
                    "formatted_mean": format_compact_metric(mean_v),
                    "formatted_total": format_compact_metric(total_v)
                }

    kpis["column_metadata"] = column_metadata
    kpis["summary_stats"] = summary_stats

    # 10. Sample Records (First 15 sanitized rows)
    clean_sample_df = df.head(15).replace({np.nan: None, np.inf: None, -np.inf: None})
    sample_records = clean_sample_df.to_dict(orient="records")
    kpis["sample_records"] = sample_records

    # 11. Pareto Concentration
    if metric_col and len(df) > 10:
        sorted_vals = df[metric_col].dropna().sort_values(ascending=False).values
        top_20_count = max(1, int(len(sorted_vals) * 0.2))
        top_share = float(sorted_vals[:top_20_count].sum())
        total_sum = float(sorted_vals.sum())
        share_pct = round((top_share / total_sum) * 100, 1) if total_sum > 0 else 0.0
        kpis["concentration"] = {
            "top_share_pct": share_pct,
            "description": f"Top 20% of records account for {share_pct}% of cumulative {metric_col.replace('_', ' ').title()}"
        }

    return kpis
