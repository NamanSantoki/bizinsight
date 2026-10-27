from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.all_models import AuditLog

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
    Persistently logs security, pipeline, and business intelligence actions into audit_logs.
    """
    log_entry = AuditLog(
        user_id=user_id,
        username=username or ("system" if not user_id else f"user_{user_id}"),
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=details or {},
        ip_address=ip_address
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
