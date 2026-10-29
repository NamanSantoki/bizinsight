"""
Enterprise Governance Approval Workflows
Manages dual-authorization for Model Deployments, PII Data Exports, and Sensitive Schema Publishing.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

class ApprovalRequest:
    def __init__(
        self,
        id: str,
        action: str,
        resource: str,
        requested_by: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "PENDING_APPROVAL",
        reviewer: Optional[str] = None,
        reviewed_at: Optional[str] = None,
        decision_note: Optional[str] = None
    ):
        self.id = id
        self.action = action
        self.resource = resource
        self.requested_by = requested_by
        self.requested_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self.reason = reason
        self.metadata = metadata or {}
        self.status = status
        self.reviewer = reviewer
        self.reviewed_at = reviewed_at
        self.decision_note = decision_note

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "resource": self.resource,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at,
            "reason": self.reason,
            "metadata": self.metadata,
            "status": self.status,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "decision_note": self.decision_note
        }

class ApprovalWorkflowEngine:
    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}
        self._seed_default_requests()

    def _seed_default_requests(self):
        req1 = ApprovalRequest(
            id="REQ-8491",
            action="EXPORT_PII_DATASET",
            resource="Customer Master Fact (1.28M rows)",
            requested_by="analyst",
            reason="External regulatory compliance audit for GDPR Article 30 registry",
            metadata={"rows": 1284392, "pii_present": True, "classification": "Confidential"},
            status="PENDING_APPROVAL"
        )
        req2 = ApprovalRequest(
            id="REQ-7210",
            action="MODEL_DEPLOYMENT",
            resource="Revenue Forecast Model v7 (XGBoost)",
            requested_by="ml_engineer",
            reason="Model achieved 94.2% accuracy on validation set and passed drift & fairness benchmarks",
            metadata={"accuracy": "94.2%", "drift": "Low", "target_env": "PRODUCTION"},
            status="APPROVED",
            reviewer="admin",
            reviewed_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            decision_note="Governance gate verified; all unit tests and explainability checks cleared."
        )
        self._requests[req1.id] = req1
        self._requests[req2.id] = req2

    def list_requests(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._requests.values()]

    def create_request(self, action: str, resource: str, requested_by: str, reason: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        req_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
        req = ApprovalRequest(
            id=req_id,
            action=action,
            resource=resource,
            requested_by=requested_by,
            reason=reason,
            metadata=metadata
        )
        self._requests[req_id] = req
        return req.to_dict()

    def review_request(self, request_id: str, reviewer: str, approve: bool, note: str = "") -> Dict[str, Any]:
        req = self._requests.get(request_id)
        if not req:
            return {"error": f"Request {request_id} not found."}

        if req.requested_by == reviewer:
            return {"error": "Separation of Duties violation: requester cannot approve their own submission."}

        req.status = "APPROVED" if approve else "REJECTED"
        req.reviewer = reviewer
        req.reviewed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        req.decision_note = note
        return req.to_dict()

approval_engine = ApprovalWorkflowEngine()

