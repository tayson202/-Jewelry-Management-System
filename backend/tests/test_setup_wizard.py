import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, SystemSetting
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_headers():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    admin = db.query(User).filter(User.role == "ADMIN", User.is_active == True).first()
    if not admin:
        admin = User(
            email="setup_admin_test@3mdahab.com",
            full_name="Setup Admin Test",
            hashed_password=get_password_hash("AdminPass123!"),
            role="ADMIN",
            token_version=1
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    token = create_access_token(subject=admin.id, role="ADMIN", token_version=admin.token_version)
    db.close()
    return {"Authorization": f"Bearer {token}"}

def test_setup_status_endpoint():
    res = client.get("/api/v1/setup/status")
    assert res.status_code == 200
    data = res.json()
    assert "is_initialized" in data
    assert "has_admin" in data
    assert "shop_configured" in data
    assert "shop_profile" in data
    assert data["shop_profile"]["default_currency"] == "EGP"
    assert data["shop_profile"]["timezone"] == "Africa/Cairo"

def test_setup_init_admin_lockout_when_admin_exists():
    # Since an active admin exists in the fixture DB, init-admin must be strictly rejected with 403 Forbidden!
    payload = {
        "email": "unauthorized_takeover@example.com",
        "full_name": "Attacker",
        "password": "Password123!",
        "pin": "9999"
    }
    res = client.post("/api/v1/setup/init-admin", json=payload)
    assert res.status_code == 403
    assert "already has an active admin" in res.json()["detail"].lower()

def test_setup_shop_profile_configuration(admin_headers):
    payload = {
        "shop_name": "3M Dahab - Flagship Cairo",
        "shop_phone": "+20 100 123 4567",
        "shop_address": "Khan El-Khalili, Cairo, Egypt",
        "default_currency": "EGP",
        "display_language": "ar",
        "timezone": "Africa/Cairo",
        "gold_provider": "getdaleelak.com"
    }
    res = client.post("/api/v1/setup/shop-profile", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["shop_name"] == "3M Dahab - Flagship Cairo"
    assert data["shop_setup_completed"] is True

    # Re-check setup status
    status_res = client.get("/api/v1/setup/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["shop_configured"] is True
    assert status_data["shop_profile"]["shop_name"] == "3M Dahab - Flagship Cairo"
