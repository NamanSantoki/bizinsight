import pytest
import hashlib
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.ingestion.service import sanitize_table_name, RESERVED_SYSTEM_TABLES
from backend.app.audit.service import log_audit_event, verify_audit_log_chain, GENESIS_HASH
from backend.app.models.all_models import AuditLog

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_system_table_overwrite_protection():
    """Verify that user dataset tables can NEVER match or overwrite reserved system tables."""
    for reserved in RESERVED_SYSTEM_TABLES:
        safe_name = sanitize_table_name(reserved)
        assert safe_name != reserved, f"Vulnerability: Reserved table '{reserved}' was not sanitized!"
        assert safe_name.startswith("usr_ds_")
    
    # Also test numeric and space prefix handling
    assert sanitize_table_name("123_financial_data").startswith("usr_ds_")
    assert sanitize_table_name("user profiles & metrics").startswith("usr_ds_")

def test_cryptographic_audit_chain_and_tamper_detection(db_session):
    """Verify that audit logs are cryptographically linked and detect unauthorized database manipulation."""
    # Log 3 events
    e1 = log_audit_event(db_session, action="test_action_1", details={"step": 1})
    assert e1.record_hash is not None
    assert len(e1.record_hash) == 64 # SHA-256 length

    e2 = log_audit_event(db_session, action="test_action_2", details={"step": 2})
    assert e2.prev_hash == e1.record_hash
    assert e2.record_hash is not None

    e3 = log_audit_event(db_session, action="test_action_3", details={"step": 3})
    assert e3.prev_hash == e2.record_hash

    # Verify unbroken chain
    verification = verify_audit_log_chain(db_session)
    assert verification["status"] == "valid"
    assert verification["total_records"] >= 3

    # Tamper simulation: secretly alter details of e2 in database
    original_details = e2.details
    e2.details = {"step": 2, "tampered_injected_admin_grant": True}
    db_session.commit()

    # Re-verify: must catch tampering immediately!
    tamper_check = verify_audit_log_chain(db_session)
    assert tamper_check["status"] in ["tampered", "compromised"]
    assert tamper_check["compromised_id"] == e2.id

    # Restore e2 to leave db in clean state
    e2.details = original_details
    db_session.commit()

def test_health_probe(client):
    """Test enterprise readiness & liveness health probe."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert "timestamp" in data

def test_correlation_id_and_timing_headers(client):
    """Test that all responses return correlation ID and execution latency headers."""
    res = client.get("/")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert "X-Response-Time-Ms" in res.headers

