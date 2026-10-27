import os
import io
import re
import chardet
import pandas as pd
from typing import Dict, Any, Tuple
from fastapi import UploadFile, HTTPException

def sanitize_table_name(name: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().strip())
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"ds_{cleaned}"
    return cleaned[:48]

def detect_file_encoding(file_bytes: bytes) -> str:
    # Take sample of up to 64KB for speed and accuracy
    sample = file_bytes[:65536]
    result = chardet.detect(sample)
    encoding = result.get("encoding")
    if not encoding:
        return "utf-8"
    # Normalize common windows encodings
    if encoding.lower() in ["ascii", "iso-8859-1", "windows-1252"]:
        return "latin1"
    return encoding

def inspect_and_read_file(
    file_bytes: bytes, 
    filename: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Ingests CSV or Excel bytes safely:
    - Detects encoding
    - Detects delimiter (comma, semicolon, tab, pipe)
    - Inspects headers
    - Infers types, dates, numerics, categoricals
    - Never mutates raw inputs
    """
    ext = os.path.splitext(filename)[1].lower()
    encoding_detected = "utf-8"
    delimiter_detected = ","

    if ext in [".csv", ".txt"]:
        encoding_detected = detect_file_encoding(file_bytes)
        
        # Test delimiter on sample
        try:
            sample_text = file_bytes[:16384].decode(encoding_detected, errors="ignore")
            # Look for common delimiters
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
        except Exception as e:
            # Fallback with python engine
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
        # Check if column is numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_columns.append(col_str)
            continue
        
        # Check if column looks like a date
        # If string, sample non-null values
        non_null_samples = df[col].dropna().head(20).astype(str).tolist()
        is_date = False
        if non_null_samples:
            try:
                converted = pd.to_datetime(non_null_samples, errors='coerce')
                # If at least 80% successfully parsed and wasn't purely integers like IDs
                if converted.notnull().mean() > 0.8:
                    # Guard against pure numbers being interpreted as timestamps
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
