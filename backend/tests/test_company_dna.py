import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.models.all_models import User, CompanyProfile
from backend.app.security.auth import get_password_hash

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Ensure test admin user exists
    user = db.query(User).filter(User.username == "test_admin").first()
    if not user:
        user = User(
            username="test_admin",
            email="test_admin@bizinsight.local",
            hashed_password=get_password_hash("TestPass2026!"),
            role="admin"
        )
        db.add(user)
        db.commit()
    yield
    db.close()

def get_auth_token():
    res = client.post("/api/v1/auth/login", data={"username": "test_admin", "password": "TestPass2026!"})
    assert res.status_code == 200
    return res.json()["access_token"]

def test_company_taxonomies():
    res = client.get("/api/v1/company/profile/taxonomies")
    assert res.status_code == 200
    data = res.json()
    assert "sectors" in data
    assert len(data["sectors"]) >= 5
    assert "macro_sensitivities" in data
    assert len(data["macro_sensitivities"]) >= 5
    assert "standard_kpis" in data

def test_company_profile_lifecycle():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Profile
    payload = {
        "organization_name": "Global Logistics & Freight Corp",
        "industry_sector": "Manufacturing & Supply Chain",
        "business_model": "B2B Enterprise Contracts",
        "annual_revenue_bracket": "USD $100M - $500M",
        "operating_currencies": ["USD", "EUR", "SGD"],
        "geographic_regions": ["North America", "European Union", "Asia-Pacific"],
        "key_macro_sensitivities": ["crude_oil", "freight_rates", "fx_volatility"],
        "key_competitors": ["Maersk", "DHL Global", "FedEx Supply Chain"],
        "monitored_kpis": ["gross_margin", "logistics_unit_cost", "operating_cash_flow"],
        "risk_tolerance": "conservative"
    }

    create_res = client.post("/api/v1/company/profile", headers=headers, json=payload)
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["organization_name"] == "Global Logistics & Freight Corp"
    assert "crude_oil" in created["key_macro_sensitivities"]

    # 2. Get Profile
    get_res = client.get("/api/v1/company/profile", headers=headers)
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["id"] == created["id"]
    assert fetched["risk_tolerance"] == "conservative"

    # 3. Update Profile (Upsert)
    payload["risk_tolerance"] = "moderate"
    payload["organization_name"] = "Global Logistics & Freight Corp v2"
    update_res = client.post("/api/v1/company/profile", headers=headers, json=payload)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["risk_tolerance"] == "moderate"
    assert updated["organization_name"] == "Global Logistics & Freight Corp v2"

