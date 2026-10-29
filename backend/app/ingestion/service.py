import os
import io
import re
import hashlib
import chardet
import pandas as pd
from typing import Dict, Any, Tuple
from fastapi import HTTPException

RESERVED_SYSTEM_TABLES = {
    "users", "datasets", "audit_logs", "data_sources", 
    "data_quality_reports", "model_runs", "anomalies", "customer_segments",
    "alembic_version", "sqlite_master", "sqlite_sequence", "pg_catalog", "information_schema"
}

def sanitize_table_name(name: str, prefix: str = "usr_ds_") -> str:
    """
    Sanitizes dynamic table name to prevent SQL injection and guarantees
    user datasets can NEVER collide with or overwrite system tables.
    """
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().strip()).strip('_')
    if not cleaned:
        cleaned = "data"
    # Never allow matching a reserved table or starting with numeric
    if cleaned in RESERVED_SYSTEM_TABLES or cleaned[0].isdigit() or not cleaned.startswith(prefix):
        cleaned = f"{prefix}{cleaned}"
    return cleaned[:48]

def detect_file_encoding(file_bytes: bytes) -> str:
    sample = file_bytes[:65536]
    result = chardet.detect(sample)
    encoding = result.get("encoding")
    if not encoding:
        return "utf-8"
    if encoding.lower() in ["ascii", "iso-8859-1", "windows-1252"]:
        return "latin1"
    return encoding

def inspect_and_read_file(
    file_bytes: bytes, 
    filename: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Ingests CSV or Excel bytes safely:
    - Computes cryptographic SHA-256 hash for lineage & integrity
    - Detects encoding & delimiter safely
    - Infers types, dates, numerics, categoricals
    - Never mutates raw inputs
    """
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    ext = os.path.splitext(filename)[1].lower()
    encoding_detected = "utf-8"
    delimiter_detected = ","

    if ext in [".csv", ".txt"]:
        encoding_detected = detect_file_encoding(file_bytes)
        try:
            sample_text = file_bytes[:16384].decode(encoding_detected, errors="ignore")
            counts = {
                ",": sample_text.count(","),
                ";": sample_text.count(";"),
                "\t": sample_text.count("\t"),
                "|": sample_text.count("|")
            }
            delimiter_detected = max(counts, key=counts.get) if max(counts.values()) > 0 else ","
        except Exception:
            delimiter_detected = ","

        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding_detected,
                sep=delimiter_detected,
                low_memory=False
            )
        except Exception:
            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding="latin1",
                    sep=None,
                    engine="python"
                )
                encoding_detected = "latin1"
            except Exception as ex2:
                raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(ex2)}")

    elif ext in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
            encoding_detected = "binary-excel"
            delimiter_detected = "N/A"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse Excel file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file format '{ext}'. Must be CSV or Excel.")

    # Infer column roles
    date_columns = []
    numeric_columns = []
    categorical_columns = []

    for col in df.columns:
        col_str = str(col)
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_columns.append(col_str)
            continue
        
        non_null_samples = df[col].dropna().head(20).astype(str).tolist()
        is_date = False
        if non_null_samples:
            try:
                converted = pd.to_datetime(non_null_samples, errors='coerce', format='mixed')
                if converted.notnull().mean() > 0.8:
                    if not all(s.replace('.', '', 1).isdigit() for s in non_null_samples if s):
                        is_date = True
            except Exception:
                is_date = False

        if is_date or pd.api.types.is_datetime64_any_dtype(df[col]):
            date_columns.append(col_str)
        else:
            categorical_columns.append(col_str)

    metadata = {
        "filename": filename,
        "extension": ext,
        "file_hash": file_hash,
        "encoding": encoding_detected,
        "delimiter": delimiter_detected,
        "raw_rows": int(len(df)),
        "raw_columns": int(len(df.columns)),
        "columns": [str(c) for c in df.columns],
        "date_columns": date_columns,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns
    }

    return df, metadata
