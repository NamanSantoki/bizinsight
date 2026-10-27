import pandas as pd
import numpy as np
from typing import Dict, Any, List

def compute_dataset_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes rigorous dataset profile:
    - rows, cols, memory usage
    - missing values & missing percentages
    - duplicates
    - column statistics (min, max, mean, median, std, quartiles)
    - date ranges and frequencies
    - categorical distributions and top frequencies
    - IQR-based outlier counts
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    duplicate_count = int(df.duplicated().sum())
    duplicate_pct = round((duplicate_count / total_rows * 100), 2) if total_rows > 0 else 0.0

    column_profiles = {}

    for col in df.columns:
        series = df[col]
        col_type = str(series.dtype)
        null_count = int(series.isnull().sum())
        null_pct = round((null_count / total_rows * 100), 2) if total_rows > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        
        prof: Dict[str, Any] = {
            "name": str(col),
            "dtype": col_type,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "cardinality_ratio": round(unique_count / total_rows, 4) if total_rows > 0 else 0.0
        }

        # Numeric analysis
        if pd.api.types.is_numeric_dtype(series):
            clean_s = series.dropna()
            if len(clean_s) > 0:
                q25 = float(clean_s.quantile(0.25))
                q50 = float(clean_s.quantile(0.50)) # median
                q75 = float(clean_s.quantile(0.75))
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outliers = int(((clean_s < lower_bound) | (clean_s > upper_bound)).sum())

                prof["stats"] = {
                    "is_numeric": True,
                    "min": float(clean_s.min()),
                    "max": float(clean_s.max()),
                    "mean": round(float(clean_s.mean()), 4),
                    "median": round(q50, 4),
                    "std": round(float(clean_s.std()), 4) if len(clean_s) > 1 else 0.0,
                    "q25": round(q25, 4),
                    "q75": round(q75, 4),
                    "outlier_count": outliers,
                    "outlier_pct": round(outliers / len(clean_s) * 100, 2)
                }
            else:
                prof["stats"] = {"is_numeric": True, "empty": True}

        # Datetime analysis
        elif pd.api.types.is_datetime64_any_dtype(series):
            clean_s = series.dropna()
            if len(clean_s) > 0:
                prof["datetime_stats"] = {
                    "is_datetime": True,
                    "min_date": str(clean_s.min()),
                    "max_date": str(clean_s.max()),
                    "time_span_days": int((clean_s.max() - clean_s.min()).days)
                }

        # Categorical / string analysis
        else:
            val_counts = series.value_counts(dropna=True).head(5).to_dict()
            prof["top_categories"] = {str(k): int(v) for k, v in val_counts.items()}

        column_profiles[str(col)] = prof

    return {
        "dimensions": {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum())
        },
        "quality_overview": {
            "total_nulls": int(df.isnull().sum().sum()),
            "overall_null_pct": round(float(df.isnull().sum().sum()) / (total_rows * total_cols) * 100, 2) if total_rows * total_cols > 0 else 0.0,
            "duplicate_rows": duplicate_count,
            "duplicate_pct": duplicate_pct
        },
        "columns": column_profiles
    }
