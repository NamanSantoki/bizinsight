import pytest
from datetime import datetime, timezone, timedelta
from backend.app.observability.incidents import IncidentOperationsCenter
from backend.app.governance.export_governance import ExportGovernanceEngine, export_governance

def test_incident_operations_status():
    ops = IncidentOperationsCenter()
    status = ops.get_operations_status()
    assert "overall_system_status" in status
    assert len(status["services"]) >= 5
    assert len(status["active_incidents"]) >= 1

def test_incident_resolve():
    ops = IncidentOperationsCenter()
    # Resolve existing incident
    res = ops.resolve_incident("INC-1042", "Backlog cleared, throughput restored to normal.")
    assert res["status"] == "success"
    assert res["incident"]["status"] == "RESOLVED"
    assert "resolved_at" in res["incident"]

    # Non-existent incident
    err = ops.resolve_incident("INC-9999", "Notes")
    assert "error" in err

def test_export_governance_viewer_denied():
    eng = ExportGovernanceEngine()
    res = eng.request_export(
        dataset_name="sales",
        user_role="viewer",
        user_department="Sales",
        user_id="user_1",
        classification_tier="Internal",
        contains_pii=False
    )
    assert res["authorized"] is False
    assert "restricted" in res["reason"]

def test_export_governance_highly_sensitive_analyst():
    eng = ExportGovernanceEngine()
    res = eng.request_export(
        dataset_name="salaries",
        user_role="analyst",
        user_department="Finance",
        user_id="user_2",
        classification_tier="Highly Sensitive",
        contains_pii=True
    )
    assert res["authorized"] is False
    assert res["requires_approval"] is True

def test_export_governance_authorized_and_token_verification():
    eng = ExportGovernanceEngine()
    res = eng.request_export(
        dataset_name="public_data",
        user_role="analyst",
        user_department="Marketing",
        user_id="user_3",
        classification_tier="Confidential",
        contains_pii=True
    )
    assert res["authorized"] is True
    assert "download_token" in res
    assert res["pii_masked"] is True

    # Verify valid token
    token = res["download_token"]
    record = eng.verify_token(token)
    assert record is not None
    assert record["dataset_name"] == "public_data"

    # Verify invalid token
    assert eng.verify_token("invalid_token_123") is None

    # Verify expired token
    eng._active_tokens[token]["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    assert eng.verify_token(token) is None

def test_export_governance_singleton():
    assert export_governance is not None

