import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.models.all_models import AuditLog

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def compute_record_hash(
    prev_hash: str,
    created_at_str: str,
    user_id: Optional[int],
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    details: Optional[Dict[str, Any]]
) -> str:
    """Computes a deterministic cryptographic SHA-256 hash for an audit log record."""
    serialized_details = json.dumps(details or {}, sort_keys=True)
    payload = f"{prev_hash}|{created_at_str}|{user_id}|{action}|{resource_type}|{resource_id}|{serialized_details}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def format_canonical_dt(dt: Optional[datetime]) -> str:
    """Canonical string format for timestamps in cryptographic hashing."""
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def log_audit_event(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Persistently logs security, pipeline, and business intelligence actions into audit_logs
    with cryptographic SHA-256 block linkage for tamper-evidence.
    """
    last_log = db.query(AuditLog).filter(AuditLog.record_hash.isnot(None)).order_by(desc(AuditLog.id)).first()
    prev_hash = last_log.record_hash if (last_log and last_log.record_hash) else GENESIS_HASH
    
    now_utc = datetime.now(timezone.utc)
    canonical_time = format_canonical_dt(now_utc)

    current_hash = compute_record_hash(
        prev_hash=prev_hash,
        created_at_str=canonical_time,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=details
    )

    log_entry = AuditLog(
        user_id=user_id,
        username=username or ("system" if not user_id else f"user_{user_id}"),
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=details or {},
        ip_address=ip_address,
        prev_hash=prev_hash,
        record_hash=current_hash,
        created_at=now_utc
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

def verify_audit_log_chain(db: Session) -> Dict[str, Any]:
    """
    Verifies cryptographic block integrity across all cryptographically signed audit logs.
    Returns status='valid' if unbroken, or details of the first breached/tampered record.
    """
    records = db.query(AuditLog).filter(AuditLog.record_hash.isnot(None)).order_by(AuditLog.id.asc()).all()
    if not records:
        return {"status": "valid", "total_records": 0, "message": "No signed audit records present."}

    expected_prev = records[0].prev_hash
    for rec in records:
        if rec.prev_hash != expected_prev:
            return {
                "status": "compromised",
                "compromised_id": rec.id,
                "reason": f"Hash chain broken at record ID {rec.id}. Expected prev_hash {expected_prev}, got {rec.prev_hash}."
            }
        
        canonical_time = format_canonical_dt(rec.created_at)
        recomputed = compute_record_hash(
            prev_hash=rec.prev_hash,
            created_at_str=canonical_time,
            user_id=rec.user_id,
            action=rec.action,
            resource_type=rec.resource_type,
            resource_id=rec.resource_id,
            details=rec.details
        )
        if rec.record_hash != recomputed:
            return {
                "status": "tampered",
                "compromised_id": rec.id,
                "reason": f"Record payload hash mismatch at record ID {rec.id}."
            }
        
        expected_prev = rec.record_hash

    return {
        "status": "valid",
        "total_records": len(records),
        "latest_block_hash": expected_prev,
        "message": "Cryptographic audit chain fully verified. Zero tampering detected."
    }
