import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def run_rfm_segmentation(
    df: pd.DataFrame,
    customer_id_col: str,
    date_col: str,
    monetary_col: str,
    n_clusters: int = 4
) -> Dict[str, Any]:
    """
    Data-Driven Customer Segmentation via RFM (Recency, Frequency, Monetary) & K-Means:
    - Calculates Recency (days since last purchase relative to latest dataset date)
    - Calculates Frequency (total transactions per customer)
    - Calculates Monetary value (total spend)
    - Scales features and clusters using K-Means
    - Labels segments interpretably based on empirical cluster medians
    - Never claims clusters are verified psychological customer profiles
    """
    for col, name in [(customer_id_col, "Customer ID"), (date_col, "Date"), (monetary_col, "Monetary/Spend")]:
        if col not in df.columns:
            return {"error": f"Required column '{col}' ({name}) not found in dataset."}

    # Prepare data
    rfm_df = df[[customer_id_col, date_col, monetary_col]].copy()
    rfm_df[date_col] = pd.to_datetime(rfm_df[date_col], errors='coerce')
    rfm_df[monetary_col] = pd.to_numeric(rfm_df[monetary_col], errors='coerce')
    rfm_df = rfm_df.dropna()

    if len(rfm_df) == 0:
        return {"error": "No valid records after parsing Customer ID, Date, and Spend."}

    max_date = rfm_df[date_col].max()

    # Aggregate by Customer
    customer_rfm = rfm_df.groupby(customer_id_col).agg(
        recency=(date_col, lambda d: (max_date - d.max()).days),
        frequency=(monetary_col, 'count'),
        monetary=(monetary_col, 'sum')
    ).reset_index()

    if len(customer_rfm) < n_clusters * 3:
        return {
            "error": f"Insufficient distinct customers ({len(customer_rfm)}) to form {n_clusters} clusters reliably."
        }

    # Log transform to handle right-skewed spend and frequency
    rfm_log = pd.DataFrame()
    rfm_log['recency'] = np.log1p(customer_rfm['recency'].clip(lower=0))
    rfm_log['frequency'] = np.log1p(customer_rfm['frequency'].clip(lower=1))
    rfm_log['monetary'] = np.log1p(customer_rfm['monetary'].clip(lower=0))

    # Standard scale
    scaler = StandardScaler()
    scaled_feats = scaler.fit_transform(rfm_log[['recency', 'frequency', 'monetary']])

    # K-Means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    customer_rfm['cluster'] = kmeans.fit_predict(scaled_feats)

    # Compute cluster statistics
    cluster_stats = []
    overall_avg_spend = float(customer_rfm['monetary'].mean())
    overall_avg_freq = float(customer_rfm['frequency'].mean())
    overall_avg_rec = float(customer_rfm['recency'].mean())

    for c_id in range(n_clusters):
        c_sub = customer_rfm[customer_rfm['cluster'] == c_id]
        c_count = len(c_sub)
        c_rec = float(c_sub['recency'].median())
        c_freq = float(c_sub['frequency'].median())
        c_mon = float(c_sub['monetary'].median())

        # Objective label assignment based on median comparisons
        label_parts = []
        if c_mon > overall_avg_spend:
            label_parts.append("High Spend")
        else:
            label_parts.append("Moderate/Low Spend")

        if c_freq > overall_avg_freq:
            label_parts.append("Frequent")
        else:
            label_parts.append("Occasional")

        if c_rec < overall_avg_rec:
            label_parts.append("Recent")
        else:
            label_parts.append("Lapsing")

        segment_label = " - ".join(label_parts)

        cluster_stats.append({
            "cluster_id": int(c_id),
            "segment_label": segment_label,
            "customer_count": c_count,
            "percentage": round(c_count / len(customer_rfm) * 100, 2),
            "median_recency_days": round(c_rec, 1),
            "median_frequency": round(c_freq, 1),
            "median_monetary": round(c_mon, 2),
            "total_cluster_revenue": round(float(c_sub['monetary'].sum()), 2)
        })

    # Sort clusters by median monetary spend descending
    cluster_stats.sort(key=lambda x: x["median_monetary"], reverse=True)

    # Sample customer assignments
    sample_customers = [
        {
            "customer_id": str(r[customer_id_col]),
            "cluster_id": int(r['cluster']),
            "recency_days": int(r['recency']),
            "frequency_orders": int(r['frequency']),
            "total_spend": round(float(r['monetary']), 2)
        }
        for _, r in customer_rfm.head(25).iterrows()
    ]

    return {
        "status": "success",
        "methodology": "K-Means RFM (Recency, Frequency, Monetary) clustering on log-transformed scaled metrics.",
        "total_unique_customers": len(customer_rfm),
        "cluster_count": n_clusters,
        "segments": cluster_stats,
        "sample_assignments": sample_customers,
        "disclaimer": "These segments represent empirical data-driven clusters derived from historical transactions, not definitive customer personas."
    }
