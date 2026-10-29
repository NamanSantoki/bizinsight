import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "AdminPass2026!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    json = response.json()
    assert "access_token" in json
    assert json["token_type"] == "bearer"

def test_login_failure_wrong_password(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
