import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.models.all_models import User, CompanyProfile, MarketSignalEvent, CausalImpactAssessment
from backend.app.security.auth import get_password_hash

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Ensure test user
    user = db.query(User).filter(User.username == "radar_admin").first()
    if not user:
        user = User(
            username="radar_admin",
            email="radar_admin@bizinsight.local",
            hashed_password=get_password_hash("RadarPass2026!"),
            role="admin"
        )
        db.add(user)
        db.commit()

    # Ensure test company profile with crude oil & freight sensitivities
    profile = db.query(CompanyProfile).first()
    if not profile:
        profile = CompanyProfile(
            organization_name="Apex Logistics & Distribution",
            industry_sector="Manufacturing & Supply Chain",
            business_model="B2B Enterprise Contracts",
            key_macro_sensitivities=["crude_oil", "freight_rates", "interest_rates"],
            monitored_kpis=["gross_margin", "inventory_turnover"],
            risk_tolerance="conservative"
        )
        db.add(profile)
        db.commit()

    yield
    db.close()

def get_auth_token():
    res = client.post("/api/v1/auth/login", data={"username": "radar_admin", "password": "RadarPass2026!"})
    assert res.status_code == 200
    return res.json()["access_token"]

def test_market_radar_scan_and_feed():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Trigger Autonomous Market Radar Scan
    scan_res = client.post("/api/v1/market-radar/scan", headers=headers)
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["status"] == "success"
    assert scan_data["signals_processed"] > 0

    # 2. Get Market Radar Feed
    feed_res = client.get("/api/v1/market-radar/feed", headers=headers)
    assert feed_res.status_code == 200
    feed_data = feed_res.json()
    assert feed_data["configured"] is True
    assert "assessments" in feed_data
    assert len(feed_data["assessments"]) > 0

    # Verify first assessment properties
    first = feed_data["assessments"][0]
    assert "affected_kpi" in first
    assert "projected_impact_pct" in first
    assert "transmission_mechanism" in first
    assert len(first["prescribed_actions"]) > 0

    # 3. Acknowledge Assessment (Executive Sign-Off)
    ack_res = client.post(
        f"/api/v1/market-radar/assessments/{first['id']}/acknowledge",
        headers=headers,
        json={"notes": "Procurement committee convened; executing 60-day diesel collar."}
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"

def test_sensitivity_matrix():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/market-radar/sensitivity-matrix", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "matrix" in data
    assert len(data["matrix"]) >= 4
    # Check that crude_oil elasticity is negative (cost shock)
    oil_entry = next((item for item in data["matrix"] if item["factor_key"] == "crude_oil"), None)
    assert oil_entry is not None
    assert oil_entry["pass_through_elasticity"] < 0

