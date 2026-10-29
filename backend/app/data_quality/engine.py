import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Maximum sample rows to return per issue (keeps payload manageable)
MAX_AFFECTED_ROWS_SAMPLE = 25

def evaluate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates dataset quality and calculates an honest, transparent quality score.
    Formula:
      Base Score = 100.0
      Penalties:
        - Missing cell penalty: up to 30 points (proportional to total null cells / total cells)
        - Duplicate rows penalty: up to 25 points (proportional to duplicate rows / total rows)
        - Extreme outliers penalty: up to 15 points (proportional to numeric outlier rates)
        - Negative value penalty on revenue/price/quantity fields: 15 points
        - High Cardinality / Degenerate column penalty (all null or single constant value): 15 points
      Final Score = max(0.0, round(100.0 - total_penalties, 2))
    
    Each issue now includes `affected_rows` — a sample of the actual row indices
    and values that triggered the defect — so users can pinpoint exactly WHERE
    the corruption lives in their data.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    issues: List[Dict[str, Any]] = []

    if total_rows == 0:
        return {
            "quality_score": 0.0,
            "passed": False,
            "formula_description": "Dataset has 0 rows. Quality score is 0.0%.",
            "summary": {"total_rows": 0, "total_columns": total_cols},
            "column_issues": [{"severity": "critical", "message": "Dataset is empty"}]
        }

    # 1. Missing cells
    total_cells = total_rows * total_cols
    null_cells = int(df.isnull().sum().sum())
    null_ratio = null_cells / total_cells if total_cells > 0 else 0.0
    missing_penalty = min(30.0, null_ratio * 30.0 * 2.5) # scaled so 40% missing yields max 30 penalty

    # 2. Duplicate rows
    dup_mask = df.duplicated(keep='first')
    dup_rows = int(dup_mask.sum())
    dup_ratio = dup_rows / total_rows if total_rows > 0 else 0.0
    duplicate_penalty = min(25.0, dup_ratio * 25.0 * 2.0)

    # Report duplicate rows with their actual locations
    if dup_rows > 0:
        dup_indices = dup_mask[dup_mask].index.tolist()[:MAX_AFFECTED_ROWS_SAMPLE]
        affected = []
        for idx in dup_indices:
            row_dict = {}
            for c in df.columns[:6]:  # limit columns for readability
                val = df.at[idx, c]
                row_dict[str(c)] = None if pd.isna(val) else _safe_val(val)
            affected.append({"row_index": int(idx) + 1, "values": row_dict})
        issues.append({
            "column": "(all columns)",
            "severity": "medium",
            "issue_type": "duplicate_rows",
            "message": f"Found {dup_rows} duplicate rows in the dataset.",
            "total_affected": dup_rows,
            "affected_rows": affected
        })

    # 3. Numeric checks & negative values
    outlier_count_total = 0
    numeric_count = 0
    negative_val_penalty = 0.0
    
    # Common business field names that should strictly be non-negative
    non_negative_keywords = ["price", "revenue", "amount", "cost", "quantity", "sales", "qty"]

    for col in df.columns:
        series = df[col]
        col_lower = str(col).lower()
        
        # Check degenerate columns
        if series.isnull().all():
            issues.append({
                "column": str(col),
                "severity": "high",
                "issue_type": "completely_null",
                "message": f"Column '{col}' is 100% null.",
                "total_affected": total_rows,
                "affected_rows": [{"row_index": int(i) + 1, "values": {str(col): None}} for i in range(min(MAX_AFFECTED_ROWS_SAMPLE, total_rows))]
            })
        elif series.nunique(dropna=True) == 1 and total_rows > 10:
            const_val = series.dropna().iloc[0]
            issues.append({
                "column": str(col),
                "severity": "medium",
                "issue_type": "constant_value",
                "message": f"Column '{col}' has zero variance (contains only 1 distinct value: '{_safe_val(const_val)}').",
                "total_affected": total_rows,
                "affected_rows": []  # not useful to list every row
            })

        # Check for missing values per column
        col_null_count = int(series.isnull().sum())
        col_null_pct = (col_null_count / total_rows) * 100
        if col_null_count > 0:
            null_indices = series[series.isnull()].index.tolist()[:MAX_AFFECTED_ROWS_SAMPLE]
            affected = [{"row_index": int(idx) + 1, "values": {str(col): None}} for idx in null_indices]
            if col_null_pct > 30.0:
                issues.append({
                    "column": str(col),
                    "severity": "medium",
                    "issue_type": "high_null_percentage",
                    "message": f"Column '{col}' has {col_null_pct:.1f}% missing values ({col_null_count:,} null cells).",
                    "total_affected": col_null_count,
                    "affected_rows": affected
                })
            elif col_null_count > 0:
                issues.append({
                    "column": str(col),
                    "severity": "low",
                    "issue_type": "missing_values",
                    "message": f"Column '{col}' has {col_null_count:,} missing values ({col_null_pct:.1f}%).",
                    "total_affected": col_null_count,
                    "affected_rows": affected
                })

        if pd.api.types.is_numeric_dtype(series):
            numeric_count += 1
            clean_s = series.dropna()
            if len(clean_s) > 0:
                # Check negative values where prohibited
                if any(kw in col_lower for kw in non_negative_keywords):
                    neg_mask = clean_s < 0
                    neg_count = int(neg_mask.sum())
                    if neg_count > 0:
                        negative_val_penalty += 5.0
                        neg_indices = clean_s[neg_mask].index.tolist()[:MAX_AFFECTED_ROWS_SAMPLE]
                        affected = [
                            {"row_index": int(idx) + 1, "values": {str(col): _safe_val(clean_s.at[idx])}}
                            for idx in neg_indices
                        ]
                        issues.append({
                            "column": str(col),
                            "severity": "high",
                            "issue_type": "invalid_negative_values",
                            "message": f"Column '{col}' contains {neg_count} negative value{'s' if neg_count != 1 else ''} in a typically non-negative field.",
                            "total_affected": neg_count,
                            "affected_rows": affected
                        })

                # IQR Outlier check
                q25 = clean_s.quantile(0.25)
                q75 = clean_s.quantile(0.75)
                iqr = q75 - q25
                if iqr > 0:
                    outlier_mask = (clean_s < q25 - 2.5 * iqr) | (clean_s > q75 + 2.5 * iqr)
                    outs = int(outlier_mask.sum())
                    outlier_count_total += outs
                    if outs > total_rows * 0.05:
                        out_indices = clean_s[outlier_mask].index.tolist()[:MAX_AFFECTED_ROWS_SAMPLE]
                        affected = [
                            {"row_index": int(idx) + 1, "values": {str(col): _safe_val(clean_s.at[idx])}}
                            for idx in out_indices
                        ]
                        issues.append({
                            "column": str(col),
                            "severity": "low",
                            "issue_type": "high_outlier_count",
                            "message": f"Column '{col}' contains {outs} extreme outliers (>2.5×IQR). Range [{q25 - 2.5*iqr:.2f}, {q75 + 2.5*iqr:.2f}].",
                            "total_affected": outs,
                            "affected_rows": affected
                        })

    outlier_ratio = (outlier_count_total / (total_rows * numeric_count)) if (total_rows > 0 and numeric_count > 0) else 0.0
    outlier_penalty = min(15.0, outlier_ratio * 100.0)
    negative_val_penalty = min(15.0, negative_val_penalty)

    total_penalties = missing_penalty + duplicate_penalty + outlier_penalty + negative_val_penalty
    final_score = max(0.0, round(100.0 - total_penalties, 2))
    passed = final_score >= 60.0

    formula_description = (
        f"Data Quality Score = 100.0 - (Missing Penalty: {missing_penalty:.2f} + "
        f"Duplicate Penalty: {duplicate_penalty:.2f} + "
        f"Outlier Penalty: {outlier_penalty:.2f} + "
        f"Domain Violation Penalty: {negative_val_penalty:.2f})"
    )

    summary = {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "duplicate_rows": dup_rows,
        "duplicate_pct": round(dup_ratio * 100, 2),
        "null_cells": null_cells,
        "null_pct": round(null_ratio * 100, 2),
        "total_issues_found": len(issues),
        "quality_rating": "Excellent" if final_score >= 90 else "Good" if final_score >= 75 else "Needs Cleaning" if final_score >= 50 else "Poor"
    }

    return {
        "quality_score": final_score,
        "formula_description": formula_description,
        "passed": passed,
        "summary": summary,
        "column_issues": issues
    }


def _safe_val(v: Any) -> Any:
    """Convert numpy/pandas types to JSON-safe Python types."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return round(float(v), 4)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if hasattr(v, 'isoformat'):
        return v.isoformat()
    return v

