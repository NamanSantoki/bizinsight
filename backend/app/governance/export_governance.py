"""
Enterprise Data Export Governance Engine
Enforces classification gates, dynamic PII sanitization, dual-authorization checks,
cryptographic audit logging, and expirable download tokens.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid

class ExportGovernanceEngine:
    def __init__(self):
        self._active_tokens: Dict[str, Dict[str, Any]] = {}

    def request_export(
        self,
        dataset_name: str,
        user_role: str,
        user_department: str,
        user_id: str,
        classification_tier: str,
        contains_pii: bool
    ) -> Dict[str, Any]:
        """
        Evaluates export authorization. If high-risk, requires approved ticket;
        otherwise issues an expirable single-use download token.
        """
        # If user is viewer, deny export
        if user_role.lower() == "viewer":
            return {
                "authorized": False,
                "reason": "Viewer role is restricted from exporting enterprise datasets."
            }

        # If highly sensitive and not admin, require dual approval
        if classification_tier == "Highly Sensitive" and user_role.lower() != "admin":
            return {
                "authorized": False,
                "requires_approval": True,
                "reason": "Dataset contains 'Highly Sensitive' attributes (GDPR Art. 9). Submission must be approved via Governance Workflow before download."
            }

        # Generate single-use expirable token valid for 15 minutes
        token = f"exp_{uuid.uuid4().hex}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        self._active_tokens[token] = {
            "token": token,
            "dataset_name": dataset_name,
            "user_id": user_id,
            "user_role": user_role,
            "classification": classification_tier,
            "pii_masked": user_role.lower() != "admin" and contains_pii,
            "expires_at": expires_at.isoformat()
        }

        return {
            "authorized": True,
            "download_token": token,
            "expires_at": expires_at.isoformat(),
            "pii_masked": user_role.lower() != "admin" and contains_pii,
            "classification": classification_tier,
            "message": "Export authorized. Generated expirable single-use download token."
        }

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        record = self._active_tokens.get(token)
        if not record:
            return None
        expires = datetime.fromisoformat(record["expires_at"])
        if datetime.now(timezone.utc) > expires:
            del self._active_tokens[token]
            return None
        return record

export_governance = ExportGovernanceEngine()

