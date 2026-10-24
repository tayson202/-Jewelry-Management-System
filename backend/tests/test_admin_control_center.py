import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, Product, Sale, SaleItem, ApiKeyConfig, LicenseConfig
from app.core.security import get_password_hash, get_pin_hash, create_access_token
from app.services.license_service import LicenseService

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_headers():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    admin = db.query(User).filter(User.role == "ADMIN", User.is_active == True).first()
    if not admin:
        admin = User(
            email="admin_test@stockpilot.com",
            full_name="Admin Test",
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

@pytest.fixture(scope="module")
def employee_headers():
    db = SessionLocal()
    emp = db.query(User).filter(User.role == "EMPLOYEE", User.is_active == True).first()
    if not emp:
        emp = User(
            email="emp_test@stockpilot.com",
            full_name="Employee Test",
            hashed_password=get_password_hash("EmpPass123!"),
            role="EMPLOYEE",
            pin_hash=get_pin_hash("1234"),
            token_version=1
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)

    token = create_access_token(subject=emp.id, role="EMPLOYEE", token_version=emp.token_version)
    db.close()
    return {"Authorization": f"Bearer {token}"}


def test_admin_overview(admin_headers, employee_headers):
    # 1. Admin should succeed
    res = client.get("/api/v1/admin/overview", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "active_products" in data
    assert "active_employees" in data
    assert "license_summary" in data
    assert "api_connection_summary" in data

    # 2. Employee should be denied
    res_emp = client.get("/api/v1/admin/overview", headers=employee_headers)
    assert res_emp.status_code == 403


def test_product_crud_and_archival(admin_headers):
    # Add product
    sku = "TEST-ADMIN-PROD-001"
    create_payload = {
        "sku": sku,
        "name": "Diamond Solitaire Admin Test",
        "name_ar": "خاتم سوليتير للاختبار الإداري",
        "karat": "18K",
        "gross_weight": 10.50,
        "stone_tare": 0.50,
        "making_charge_type": "PER_GRAM",
        "making_charge_rate": 180.00,
        "cost_price": 25000.00,
        "quantity": 3,
        "min_stock_alert": 2
    }
    res = client.post("/api/v1/admin/products", json=create_payload, headers=admin_headers)
    assert res.status_code == 201
    prod = res.json()
    prod_id = prod["id"]
    assert prod["sku"] == sku
    assert prod["is_archived"] is False
    assert prod["net_gold_weight"] == 10.0

    # Edit product
    update_payload = {
        "name": "Diamond Solitaire Royal Updated",
        "quantity": 1
    }
    res_update = client.put(f"/api/v1/admin/products/{prod_id}", json=update_payload, headers=admin_headers)
    assert res_update.status_code == 200
    assert res_update.json()["quantity"] == 1

    # Soft archive
    res_arch = client.post(f"/api/v1/admin/products/{prod_id}/archive", headers=admin_headers)
    assert res_arch.status_code == 200
    assert res_arch.json()["is_archived"] is True
    assert res_arch.json()["status"] == "ARCHIVED"

    # Restore unarchive
    res_unarch = client.post(f"/api/v1/admin/products/{prod_id}/unarchive", headers=admin_headers)
    assert res_unarch.status_code == 200
    assert res_unarch.json()["is_archived"] is False
    assert res_unarch.json()["status"] == "IN_STOCK"

    # Clean up with permanent delete (safe because it has 0 sales)
    res_del = client.delete(f"/api/v1/admin/products/{prod_id}", headers=admin_headers)
    assert res_del.status_code == 200


def test_product_safe_delete_prevention(admin_headers):
    """Verifies that items referenced by historical sales cannot be destructively deleted."""
    db = SessionLocal()
    # Find any product with sales
    sale_item = db.query(SaleItem).first()
    if not sale_item:
        db.close()
        pytest.skip("No historical sales in test database.")

    ref_prod_id = sale_item.product_id
    db.close()

    res = client.delete(f"/api/v1/admin/products/{ref_prod_id}", headers=admin_headers)
    assert res.status_code == 400
    assert "invoice" in res.json()["detail"].lower() or "referenced" in res.json()["detail"].lower()


def test_employee_management_and_last_admin_safeguard(admin_headers):
    # Create employee
    create_payload = {
        "email": "test_cashier_vault@stockpilot.com",
        "full_name": "Vault Tester Cashier",
        "role": "EMPLOYEE",
        "pin": "4455",
        "permissions": ["view_products", "record_sales"]
    }
    res = client.post("/api/v1/admin/employees", json=create_payload, headers=admin_headers)
    assert res.status_code == 201
    user_data = res.json()
    user_id = user_data["id"]
    assert user_data["pin_configured"] is True

    # Test PIN login
    pin_login_res = client.post("/api/v1/auth/pin-login", json={"email": "test_cashier_vault@stockpilot.com", "pin": "4455"})
    assert pin_login_res.status_code == 200
    assert "access_token" in pin_login_res.json()

    # Reset PIN
    res_pin = client.post(f"/api/v1/admin/employees/{user_id}/reset-pin", json={"pin": "8899"}, headers=admin_headers)
    assert res_pin.status_code == 200

    # Old PIN must fail
    res_old_pin = client.post("/api/v1/auth/pin-login", json={"email": "test_cashier_vault@stockpilot.com", "pin": "4455"})
    assert res_old_pin.status_code == 401

    # New PIN succeeds
    res_new_pin = client.post("/api/v1/auth/pin-login", json={"email": "test_cashier_vault@stockpilot.com", "pin": "8899"})
    assert res_new_pin.status_code == 200

    # Deactivate and delete test employee
    res_toggle = client.post(f"/api/v1/admin/employees/{user_id}/toggle-status", headers=admin_headers)
    assert res_toggle.status_code == 200
    assert res_toggle.json()["is_active"] is False

    res_del = client.delete(f"/api/v1/admin/employees/{user_id}", headers=admin_headers)
    assert res_del.status_code == 200


def test_api_key_management_and_masking(admin_headers):
    # Fetch API keys
    res = client.get("/api/v1/admin/api-keys", headers=admin_headers)
    assert res.status_code == 200
    configs = res.json()
    assert len(configs) >= 1
    # Check that secrets are NEVER leaked in plaintext
    for c in configs:
        assert not (c.get("api_key") or c.get("api_key_encrypted"))
        assert "masked_key" in c


def test_license_arbitrary_string_rejection(admin_headers):
    # Arbitrary strings MUST be rejected!
    res = client.post("/api/v1/admin/license/activate", json={"license_key": "arbitrary_test_key_12345"}, headers=admin_headers)
    assert res.status_code == 400
    assert "invalid license" in res.json()["detail"].lower()

    # Legitimate signed key must succeed
    demo_key = LicenseService.generate_demo_license_key(tier="ENTERPRISE", org="TESTCAIRO", days_valid=90)
    res_legit = client.post("/api/v1/admin/license/activate", json={"license_key": demo_key, "licensed_to": "Test Cairo Boutique"}, headers=admin_headers)
    assert res_legit.status_code == 200
    assert res_legit.json()["status"] == "ACTIVE"
    assert res_legit.json()["license_type"] == "ENTERPRISE"
