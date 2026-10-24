import json
import re
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash, get_pin_hash
from app.models import User, SystemSetting, ApiKeyConfig, AuditLog
from app.api.deps import require_admin

router = APIRouter(prefix="/setup", tags=["First-Time Setup Wizard"])

class InitAdminRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    pin: Optional[str] = Field(None, min_length=4, max_length=6)

class ShopProfileRequest(BaseModel):
    shop_name: str = Field(..., min_length=2, max_length=255)
    shop_phone: Optional[str] = None
    shop_address: Optional[str] = None
    shop_logo_url: Optional[str] = None
    default_currency: str = "EGP"
    display_language: str = "ar"  # 'ar' or 'en'
    timezone: str = "Africa/Cairo"
    gold_provider: Optional[str] = "getdaleelak.com"
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None

@router.get("/status")
def get_setup_status(db: Session = Depends(get_db)):
    """
    Public endpoint: Checks whether the shop has been initialized with an Admin account
    and whether the initial shop profile wizard has been completed.
    """
    admin_exists = db.query(User).filter(User.role == "ADMIN", User.is_active == True).first() is not None
    
    # Check shop name setting
    shop_name_setting = db.query(SystemSetting).filter(SystemSetting.setting_key == "shop_name").first()
    shop_phone_setting = db.query(SystemSetting).filter(SystemSetting.setting_key == "shop_phone").first()
    shop_address_setting = db.query(SystemSetting).filter(SystemSetting.setting_key == "shop_address").first()
    shop_logo_setting = db.query(SystemSetting).filter(SystemSetting.setting_key == "shop_logo_url").first()
    currency_setting = db.query(SystemSetting).filter(SystemSetting.setting_key == "default_currency").first()
    lang_setting = db.query(SystemSetting).filter(SystemSetting.setting_key == "display_language").first()
    tz_setting = db.query(SystemSetting).filter(SystemSetting.setting_key == "timezone").first()
    setup_done_setting = db.query(SystemSetting).filter(SystemSetting.setting_key == "shop_setup_completed").first()

    shop_configured = bool(setup_done_setting and setup_done_setting.setting_value.lower() == "true")

    active_provider = db.query(ApiKeyConfig).filter(ApiKeyConfig.is_active == True).first()

    return {
        "is_initialized": admin_exists,
        "has_admin": admin_exists,
        "shop_configured": shop_configured,
        "shop_profile": {
            "shop_name": shop_name_setting.setting_value if shop_name_setting else "3M Dahab OS",
            "shop_phone": shop_phone_setting.setting_value if shop_phone_setting else "",
            "shop_address": shop_address_setting.setting_value if shop_address_setting else "",
            "shop_logo_url": shop_logo_setting.setting_value if shop_logo_setting else "",
            "default_currency": currency_setting.setting_value if currency_setting else "EGP",
            "display_language": lang_setting.setting_value if lang_setting else "ar",
            "timezone": tz_setting.setting_value if tz_setting else "Africa/Cairo",
            "gold_provider": active_provider.provider_name if active_provider else "getdaleelak.com"
        }
    }

@router.post("/init-admin", status_code=status.HTTP_201_CREATED)
def initialize_primary_admin(payload: InitAdminRequest, db: Session = Depends(get_db)):
    """
    Secure One-Time Bootstrap: Allows provisioning the initial Admin account
    if and only if NO active admin currently exists. Once created, permanently locked.
    """
    existing_admin = db.query(User).filter(User.role == "ADMIN", User.is_active == True).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System already has an active Admin account. Initial setup is locked."
        )

    # Password complexity check
    pw = payload.password
    if len(pw) < 8 or not any(c.isdigit() for c in pw) or not any(c.isalpha() for c in pw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain both letters and numbers."
        )

    # Check PIN format if supplied
    pin_hash = None
    if payload.pin:
        if not re.match(r"^\d{4,6}$", payload.pin):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PIN must be 4 to 6 numeric digits."
            )
        pin_hash = get_pin_hash(payload.pin)

    # All admin permissions
    all_perms = [
        "view_products", "add_products", "edit_products", "view_stock",
        "record_sales", "view_sales_history", "view_gold_prices",
        "manage_products", "manage_employees", "manage_api_keys",
        "manage_licenses", "view_audit_logs", "modify_settings"
    ]

    new_admin = User(
        email=payload.email.strip().lower(),
        full_name=payload.full_name.strip(),
        hashed_password=get_password_hash(payload.password),
        role="ADMIN",
        pin_hash=pin_hash,
        permissions=json.dumps(all_perms),
        is_active=True,
        token_version=1
    )
    db.add(new_admin)
    db.flush()

    audit = AuditLog(
        user_id=new_admin.id,
        action="INITIALIZE_PRIMARY_ADMIN",
        entity="User",
        entity_id=new_admin.id,
        details=f"Secure primary admin provisioned for {new_admin.email}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Primary Admin account provisioned successfully.",
        "admin_id": new_admin.id,
        "email": new_admin.email,
        "full_name": new_admin.full_name
    }

@router.post("/shop-profile")
def save_shop_profile(
    payload: ShopProfileRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Authenticated First-Time Setup Wizard Step: Saves real shop metadata,
    currency, language, timezone, and market provider configurations.
    """
    settings_map = {
        "shop_name": (payload.shop_name.strip(), "Official registered shop name"),
        "shop_phone": (payload.shop_phone.strip() if payload.shop_phone else "", "Shop contact telephone number"),
        "shop_address": (payload.shop_address.strip() if payload.shop_address else "", "Physical shop or boutique address"),
        "shop_logo_url": (payload.shop_logo_url.strip() if payload.shop_logo_url else "", "URL or path to shop logo"),
        "default_currency": (payload.default_currency.strip().upper(), "Base shop currency (ISO 4217)"),
        "display_language": (payload.display_language.strip().lower(), "Preferred UI language (ar/en)"),
        "timezone": (payload.timezone.strip(), "Operational timezone (e.g. Africa/Cairo)"),
        "shop_setup_completed": ("true", "Flag indicating initial setup wizard completed")
    }

    for key, (val, desc) in settings_map.items():
        setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
        if setting:
            setting.setting_value = val
            setting.updated_at = datetime.now(timezone.utc)
            setting.updated_by = admin.id
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=val,
                description=desc,
                updated_by=admin.id
            )
            db.add(setting)

    # Optional: Configure or update Gold Price Provider
    if payload.gold_provider:
        prov = payload.gold_provider.strip().lower()
        endpoint = payload.api_endpoint or (
            "https://getdaleelak.com/api/v1/feed.json" if "daleelak" in prov
            else "https://goldpricestoday.net/api/v1/egypt.json"
        )
        api_cfg = db.query(ApiKeyConfig).filter(ApiKeyConfig.is_active == True).first()
        if not api_cfg:
            api_cfg = ApiKeyConfig(
                provider_name=prov,
                endpoint_url=endpoint,
                masked_key="PUBLIC-FREE-ACCESS" if not payload.api_key else f"••••••••{payload.api_key[-4:]}",
                is_active=True,
                validation_status="UNTESTED"
            )
            db.add(api_cfg)
        else:
            api_cfg.provider_name = prov
            api_cfg.endpoint_url = endpoint
            if payload.api_key:
                api_cfg.masked_key = f"••••••••{payload.api_key[-4:]}"
            api_cfg.updated_at = datetime.now(timezone.utc)
            api_cfg.updated_by = admin.id

    audit = AuditLog(
        user_id=admin.id,
        action="UPDATE_SHOP_PROFILE",
        entity="SystemSetting",
        details=f"Shop profile configured: {payload.shop_name} ({payload.default_currency}, {payload.display_language})"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Shop profile and setup configuration saved successfully.",
        "shop_name": payload.shop_name,
        "default_currency": payload.default_currency,
        "display_language": payload.display_language,
        "timezone": payload.timezone,
        "shop_setup_completed": True
    }
