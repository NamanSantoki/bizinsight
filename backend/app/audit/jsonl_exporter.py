import os
import json
from datetime import datetime

# Ensure the audit logs directory exists
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "audit")
os.makedirs(LOG_DIR, exist_ok=True)

def write_audit_log_jsonl(entry: dict):
    """Append a single audit entry to a JSONL file.
    The filename is `audit_<date>.jsonl` (UTC date)."""
    utc_date = datetime.utcnow().strftime("%Y-%m-%d")
    log_path = os.path.join(LOG_DIR, f"audit_{utc_date}.jsonl")
    # Serialize with minimal whitespace for compactness
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def log_nlq_query(user_role: str, dataset_id: str, nl_query: str, sql: str, **kwargs):
    """Log an NLQ query event for governance and audit trail."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "NLQ_QUERY",
        "user_role": user_role,
        "dataset_id": dataset_id,
        "nl_query": nl_query,
        "sql": sql,
        **kwargs
    }
    write_audit_log_jsonl(entry)
