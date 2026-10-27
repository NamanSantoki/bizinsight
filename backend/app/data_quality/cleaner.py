import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

def clean_dataset(
    df: pd.DataFrame,
    remove_duplicates: bool = True,
    missing_strategy: str = "none", # "none", "drop", "median_mode", "forward_fill"
    clean_column_names: bool = True,
    normalize_dates: bool = True,
    date_columns: List[str] = None,
    outlier_handling: str = "none",  # "none", "clip_iqr"
    numeric_columns: List[str] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Applies auditable, transparent data cleaning transformations.
    Logs every single action taken so data transformations are completely reproducible.
    """
    cleaned_df = df.copy()
    logs: List[str] = []

    # 1. Clean Column Names
    if clean_column_names:
        old_cols = list(cleaned_df.columns)
        new_cols = []
        for c in old_cols:
            clean_c = re.sub(r'[^a-zA-Z0-9_]', '_', str(c).strip().lower())
            clean_c = re.sub(r'_+', '_', clean_c).strip('_')
            new_cols.append(clean_c if clean_c else "unnamed_col")
        
        # Ensure unique column names if duplicates created
        seen = {}
        unique_new_cols = []
        for c in new_cols:
            if c in seen:
                seen[c] += 1
                unique_new_cols.append(f"{c}_{seen[c]}")
            else:
                seen[c] = 0
                unique_new_cols.append(c)

        if unique_new_cols != old_cols:
            cleaned_df.columns = unique_new_cols
            logs.append(f"Standardized and snake_cased {len(old_cols)} column names.")

    # 2. Duplicate Removal
    if remove_duplicates:
        initial_count = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates()
        dropped = initial_count - len(cleaned_df)
        if dropped > 0:
            logs.append(f"Removed {dropped} duplicate rows (rows changed: {initial_count} -> {len(cleaned_df)}).")
        else:
            logs.append("No duplicate rows found.")

    # 3. Normalize Date Columns
    if normalize_dates:
        target_dates = date_columns or []
        if not target_dates:
            # Auto-detect date candidate columns
            for col in cleaned_df.columns:
                col_lower = str(col).lower()
                if any(kw in col_lower for kw in ["date", "time", "timestamp", "dt", "year"]):
                    target_dates.append(str(col))

        for d_col in target_dates:
            if d_col in cleaned_df.columns:
                try:
                    converted = pd.to_datetime(cleaned_df[d_col], errors='coerce')
                    valid_pct = converted.notnull().mean()
                    if valid_pct > 0.5:
                        cleaned_df[d_col] = converted
                        logs.append(f"Normalized column '{d_col}' to ISO datetime (validity: {valid_pct*100:.1f}%).")
                except Exception as e:
                    logs.append(f"Could not convert '{d_col}' to datetime: {str(e)}")

    # 4. Handle Missing Values
    if missing_strategy == "drop":
        before_drop = len(cleaned_df)
        cleaned_df = cleaned_df.dropna()
        logs.append(f"Dropped rows with any missing values ({before_drop} -> {len(cleaned_df)} rows).")

    elif missing_strategy == "median_mode":
        imputed_summary = []
        for col in cleaned_df.columns:
            null_count = cleaned_df[col].isnull().sum()
            if null_count > 0:
                if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    median_val = cleaned_df[col].median()
                    cleaned_df[col] = cleaned_df[col].fillna(median_val)
                    imputed_summary.append(f"'{col}' (numeric): filled {null_count} nulls with median ({median_val})")
                elif pd.api.types.is_datetime64_any_dtype(cleaned_df[col]):
                    cleaned_df[col] = cleaned_df[col].ffill().bfill()
                    imputed_summary.append(f"'{col}' (datetime): ffilled {null_count} nulls")
                else:
                    mode_val = cleaned_df[col].mode(dropna=True)
                    val = mode_val.iloc[0] if len(mode_val) > 0 else "Unknown"
                    cleaned_df[col] = cleaned_df[col].fillna(val)
                    imputed_summary.append(f"'{col}' (categorical): filled {null_count} nulls with mode ('{val}')")
        
        if imputed_summary:
            logs.append("Imputed missing values: " + "; ".join(imputed_summary))

    elif missing_strategy == "forward_fill":
        cleaned_df = cleaned_df.ffill().bfill()
        logs.append("Applied forward and backward fill across missing records.")

    # 5. Outlier Treatment (Clip IQR)
    if outlier_handling == "clip_iqr":
        num_cols = numeric_columns or [c for c in cleaned_df.columns if pd.api.types.is_numeric_dtype(cleaned_df[c])]
        clipped_cols = []
        for col in num_cols:
            if col in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[col]):
                q25 = cleaned_df[col].quantile(0.25)
                q75 = cleaned_df[col].quantile(0.75)
                iqr = q75 - q25
                if iqr > 0:
                    lower = q25 - 2.5 * iqr
                    upper = q75 + 2.5 * iqr
                    initial_outliers = ((cleaned_df[col] < lower) | (cleaned_df[col] > upper)).sum()
                    if initial_outliers > 0:
                        cleaned_df[col] = cleaned_df[col].clip(lower=lower, upper=upper)
                        clipped_cols.append(f"'{col}' ({initial_outliers} values clipped to [{lower:.2f}, {upper:.2f}])")
        if clipped_cols:
            logs.append("Treated extreme outliers via IQR clipping: " + "; ".join(clipped_cols))

    return cleaned_df, logs
