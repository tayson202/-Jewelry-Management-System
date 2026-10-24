"""
3M Dahab OS - Production Initialization Script
Prepares a clean, production-ready environment for a new gold shop.
Initializes database schema, standard categories, and regulatory system settings.
Does NOT create demo products, fake sales, or mock records.
"""

import os
import sys
import argparse
import json
from decimal import Decimal
from datetime import datetime, timezone

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash, get_pin_hash
from app.models import (
    User, Category, SystemSetting, ApiKeyConfig, LicenseConfig
)
from app.services.license_service import LicenseService

def init_production(
    admin_email: str = None,
    admin_password: str = None,
    admin_name: str = None,
    admin_pin: str = None,
    shop_name: str = "3M Dahab OS"
):
    print("=" * 70)
    print(" 3M Dahab OS - Production Environment Initialization")
    print("=" * 70)

    # 1. Ensure tables exist
    print("[1/5] Verifying database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 2. Standard categories
        print("[2/5] Initializing official jewelry categories...")
        categories_data = [
            {"name": "Rings", "name_ar": "خواتم", "slug": "rings", "making": Decimal("180.00"), "margin": Decimal("12.00")},
            {"name": "Necklaces & Chains", "name_ar": "عقود وسلاسل", "slug": "necklaces", "making": Decimal("195.00"), "margin": Decimal("12.00")},
            {"name": "Bracelets & Bangles", "name_ar": "أساور وبناجر", "slug": "bangles", "making": Decimal("190.00"), "margin": Decimal("15.00")},
            {"name": "Bullion & Coins", "name_ar": "سبائك وعملات", "slug": "bullion", "making": Decimal("45.00"), "margin": Decimal("5.00")},
            {"name": "Earrings", "name_ar": "أقراط وحلقان", "slug": "earrings", "making": Decimal("250.00"), "margin": Decimal("18.00")}
        ]

        for cat_info in categories_data:
            existing = db.query(Category).filter(Category.slug == cat_info["slug"]).first()
            if not existing:
                cat = Category(
                    name=cat_info["name"],
                    name_ar=cat_info["name_ar"],
                    slug=cat_info["slug"],
                    default_making_charge=cat_info["making"],
                    floor_margin_pct=cat_info["margin"]
                )
                db.add(cat)
        db.flush()

        # 3. Regulatory System Settings (Egyptian ETA Law #67/2016 & Assay Directorate)
        print("[3/5] Applying regulatory settings and shop parameters...")
        default_settings = [
            ("shop_name", shop_name, "Official registered jewelry shop name"),
            ("default_currency", "EGP", "Base currency (Egyptian Pound)"),
            ("display_language", "ar", "Default display language (Arabic)"),
            ("timezone", "Africa/Cairo", "Operational timezone"),
            ("eta_vat_making_pct", "14.0", "Egyptian ETA VAT percentage applied exclusively to workmanship (Law #67/2016)"),
            ("max_cashier_discount_pct", "5.0", "Maximum discount cashier can apply without manager authorization"),
            ("enforce_laser_hallmark", "true", "Require official Laser Hallmark QR Code on tax invoices"),
            ("session_idle_timeout_min", "60", "POS workstation auto-lock idle timeout in minutes"),
            ("allow_scrap_tradein_without_id", "false", "Require national ID for customer scrap gold buy-backs over 5,000 EGP"),
            ("shop_setup_completed", "false", "Flag for first-time launch setup wizard")
        ]

        for key, val, desc in default_settings:
            existing = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
            if not existing:
                db.add(SystemSetting(setting_key=key, setting_value=val, description=desc))
        db.flush()

        # 4. Market Feed Provider Config (Defaulting to official Sagha feed endpoint)
        print("[4/5] Initializing gold price market provider config...")
        existing_api = db.query(ApiKeyConfig).filter(ApiKeyConfig.provider_name == "getdaleelak.com").first()
        if not existing_api:
            api_cfg = ApiKeyConfig(
                provider_name="getdaleelak.com",
                endpoint_url="https://getdaleelak.com/api/v1/feed.json",
                masked_key="PUBLIC-FREE-ACCESS",
                is_active=True,
                validation_status="UNTESTED"
            )
            db.add(api_cfg)
        db.flush()

        # 5. Admin Provisioning
        print("[5/5] Checking Admin account status...")
        existing_admin = db.query(User).filter(User.role == "ADMIN", User.is_active == True).first()

        if existing_admin:
            print(f" -> Active Admin already exists: {existing_admin.email} ({existing_admin.full_name})")
        elif admin_email and admin_password:
            admin_perms = [
                "view_products", "add_products", "edit_products", "view_stock",
                "record_sales", "view_sales_history", "view_gold_prices",
                "manage_products", "manage_employees", "manage_api_keys",
                "manage_licenses", "view_audit_logs", "modify_settings"
            ]
            pin_h = get_pin_hash(admin_pin) if admin_pin else None
            admin_user = User(
                email=admin_email.strip().lower(),
                full_name=admin_name.strip() if admin_name else "Shop Admin",
                hashed_password=get_password_hash(admin_password),
                role="ADMIN",
                pin_hash=pin_h,
                permissions=json.dumps(admin_perms),
                is_active=True,
                token_version=1
            )
            db.add(admin_user)
            db.flush()

            # Mark setup as completed if admin was explicitly configured
            setup_flag = db.query(SystemSetting).filter(SystemSetting.setting_key == "shop_setup_completed").first()
            if setup_flag:
                setup_flag.setting_value = "true"

            print(f" -> Successfully provisioned primary Admin: {admin_user.email}")
        else:
            print(" -> No Admin configured. First-Time Setup Wizard is enabled on first browser launch.")

        db.commit()
        print("\n[OK] 3M Dahab OS production database initialized successfully.")
        print("  Workspace: Empty business state (0 products, 0 fake sales, 0 fake customers).")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to initialize production database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize clean production database for 3M Dahab OS")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--password", help="Admin secure password (min 8 chars)")
    parser.add_argument("--name", help="Admin full name")
    parser.add_argument("--pin", help="Admin 4-digit PIN")
    parser.add_argument("--shop-name", default="3M Dahab OS", help="Shop business name")

    args = parser.parse_args()
    init_production(
        admin_email=args.email or os.getenv("ADMIN_EMAIL"),
        admin_password=args.password or os.getenv("ADMIN_PASSWORD"),
        admin_name=args.name or os.getenv("ADMIN_NAME"),
        admin_pin=args.pin or os.getenv("ADMIN_PIN"),
        shop_name=args.shop_name
    )
