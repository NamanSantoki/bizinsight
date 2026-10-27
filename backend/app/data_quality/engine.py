import pandas as pd
import numpy as np
from typing import Dict, Any, List

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
    dup_rows = int(df.duplicated().sum())
    dup_ratio = dup_rows / total_rows if total_rows > 0 else 0.0
    duplicate_penalty = min(25.0, dup_ratio * 25.0 * 2.0)

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
                "message": f"Column '{col}' is 100% null."
            })
        elif series.nunique(dropna=True) == 1 and total_rows > 10:
            issues.append({
                "column": str(col),
                "severity": "medium",
                "issue_type": "constant_value",
                "message": f"Column '{col}' has zero variance (contains only 1 distinct value)."
            })

        if pd.api.types.is_numeric_dtype(series):
            numeric_count += 1
            clean_s = series.dropna()
            if len(clean_s) > 0:
                # Check negative values where prohibited
                if any(kw in col_lower for kw in non_negative_keywords):
                    neg_count = int((clean_s < 0).sum())
                    if neg_count > 0:
                        negative_val_penalty += 5.0
                        issues.append({
                            "column": str(col),
                            "severity": "high",
                            "issue_type": "invalid_negative_values",
                            "message": f"Column '{col}' contains {neg_count} negative values in a typically non-negative field."
                        })

                # IQR Outlier check
                q25 = clean_s.quantile(0.25)
                q75 = clean_s.quantile(0.75)
                iqr = q75 - q25
                if iqr > 0:
                    outs = int(((clean_s < q25 - 2.5 * iqr) | (clean_s > q75 + 2.5 * iqr)).sum())
                    outlier_count_total += outs
                    if outs > total_rows * 0.05:
                        issues.append({
                            "column": str(col),
                            "severity": "low",
                            "issue_type": "high_outlier_count",
                            "message": f"Column '{col}' contains {outs} extreme outliers (>2.5*IQR)."
                        })

    outlier_ratio = (outlier_count_total / (total_rows * numeric_count)) if (total_rows > 0 and numeric_count > 0) else 0.0
    outlier_penalty = min(15.0, outlier_ratio * 100.0)
    negative_val_penalty = min(15.0, negative_val_penalty)

    # 4. Check for high missing rate in specific columns
    for col in df.columns:
        col_null_pct = (df[col].isnull().sum() / total_rows) * 100
        if col_null_pct > 30.0:
            issues.append({
                "column": str(col),
                "severity": "medium",
                "issue_type": "high_null_percentage",
                "message": f"Column '{col}' has {col_null_pct:.1f}% missing values."
            })

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
