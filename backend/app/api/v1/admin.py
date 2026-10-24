import json
import secrets
import string
import httpx
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_password_hash, get_pin_hash
from app.models import (
    User, Product, SaleItem, Sale, GoldPrice,
    AuditLog, ApiKeyConfig, LicenseConfig, SystemSetting
)
from app.schemas import (
    UserResponse, EmployeeCreateRequest, EmployeeUpdateRequest,
    PasswordResetRequest, PinResetRequest,
    ProductResponse, ProductAdminCreate, ProductAdminUpdate,
    ApiKeyConfigResponse, ApiKeyUpdateRequest, ApiKeyTestRequest,
    LicenseStatusResponse, LicenseActivateRequest,
    SystemSettingResponse, SystemSettingsUpdateRequest,
    AuditLogItemResponse, AdminOverviewResponse
)
from app.api.deps import require_admin, get_current_user
from app.services.license_service import LicenseService
from app.services.pricing_engine import KARAT_PURITY_RATIOS, round_money, round_weight

router = APIRouter(prefix="/admin", tags=["Admin Control Center"])

AVAILABLE_PERMISSIONS = [
    {"key": "view_products", "name": "View Products Catalog", "category": "Inventory"},
    {"key": "add_products", "name": "Add Pieces to Vault", "category": "Inventory"},
    {"key": "edit_products", "name": "Edit Catalog Products", "category": "Inventory"},
    {"key": "view_stock", "name": "View Inventory Quantities", "category": "Inventory"},
    {"key": "record_sales", "name": "Operate POS & Execute Sales", "category": "POS"},
    {"key": "view_sales_history", "name": "View Invoices & Sales Ledger", "category": "POS"},
    {"key": "view_gold_prices", "name": "View Live Sagha Gold Board", "category": "Market"},
    {"key": "manage_products", "name": "Full Product Archival & Deletion", "category": "Admin"},
    {"key": "manage_employees", "name": "Manage Staff & Reset Credentials", "category": "Admin"},
    {"key": "manage_api_keys", "name": "Configure Market Feed Credentials", "category": "Admin"},
    {"key": "manage_licenses", "name": "Activate & Manage System License", "category": "Admin"},
    {"key": "view_audit_logs", "name": "Inspect Immutable Security Trail", "category": "Security"},
    {"key": "modify_settings", "name": "Configure ETA VAT & Discount Caps", "category": "System"},
]

def mask_secret(secret: Optional[str]) -> str:
    """Masks secret to '••••••••AB12' format, never returning raw key."""
    if not secret:
        return "••••••••UNSET"
    clean = secret.strip()
    if len(clean) <= 4:
        return "••••" + clean
    return "••••••••" + clean[-4:]

# ==============================================================================
# SECTION 1: Overview & Executive Summary Cards
# ==============================================================================
@router.get("/overview", response_model=AdminOverviewResponse)
def get_admin_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    active_products = db.query(Product).filter(Product.is_archived == False).count()
    archived_products = db.query(Product).filter(Product.is_archived == True).count()
    low_stock_alerts = db.query(Product).filter(
        Product.is_archived == False,
        Product.quantity <= Product.min_stock_alert,
        Product.status == "IN_STOCK"
    ).count()

    active_employees = db.query(User).filter(User.is_active == True).count()
    total_employees = db.query(User).count()

    license_info = LicenseService.get_license_status(db)

    active_api = db.query(ApiKeyConfig).filter(ApiKeyConfig.is_active == True).first()
    api_summary = {
        "configured": bool(active_api),
        "provider": active_api.provider_name if active_api else "getdaleelak.com (Public Feed)",
        "endpoint": active_api.endpoint_url if active_api else "https://getdaleelak.com/api/v1/feed.json",
        "masked_key": active_api.masked_key if active_api else "PUBLIC-FREE-ACCESS",
        "validation_status": active_api.validation_status if active_api else "VALID",
        "last_tested": active_api.last_tested_at if active_api else datetime.now(timezone.utc)
    }

    recent_audits_raw = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(8).all()
    recent_audits = []
    for a in recent_audits_raw:
        u_name = a.user.full_name if a.user else "System Automation"
        u_email = a.user.email if a.user else None
        recent_audits.append(AuditLogItemResponse(
            id=a.id,
            timestamp=a.created_at,
            user_name=u_name,
            user_email=u_email,
            action=a.action,
            entity=a.entity,
            entity_id=a.entity_id,
            details=a.details,
            outcome=getattr(a, "outcome", "SUCCESS"),
            safe_metadata=getattr(a, "safe_metadata", None)
        ))

    return AdminOverviewResponse(
        active_products=active_products,
        archived_products=archived_products,
        low_stock_alerts=low_stock_alerts,
        active_employees=active_employees,
        total_employees=total_employees,
        license_summary=license_info,
        api_connection_summary=api_summary,
        recent_audits=recent_audits
    )


# ==============================================================================
# SECTION 2: Product Management (CRUD, Archival, Safe Delete, History)
# ==============================================================================
@router.get("/products", response_model=List[ProductResponse])
def list_admin_products(
    search: Optional[str] = None,
    karat: Optional[str] = None,
    status_filter: Optional[str] = None,
    include_archived: bool = True,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    query = db.query(Product)
    if not include_archived:
        query = query.filter(Product.is_archived == False)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Product.name.ilike(s)) | (Product.sku.ilike(s)) | (Product.name_ar.ilike(s)))
    if karat and karat != "ALL":
        query = query.filter(Product.karat == karat)
    if status_filter and status_filter != "ALL":
        query = query.filter(Product.status == status_filter)

    return query.order_by(Product.is_archived.asc(), Product.created_at.desc()).all()

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def admin_create_product(
    item_in: ProductAdminCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    existing = db.query(Product).filter(Product.sku == item_in.sku.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"A product with SKU '{item_in.sku}' already exists.")

    gross = item_in.gross_weight
    tare = item_in.stone_tare
    if tare > gross:
        raise HTTPException(status_code=400, detail="Stone tare weight cannot exceed gross weight.")

    net_gold = round_weight(gross - tare)
    ratio = KARAT_PURITY_RATIOS.get(item_in.karat, Decimal("0.875"))
    purity_pct = round_money(ratio * Decimal("100"))

    # Fetch spot rate
    gp = db.query(GoldPrice).filter(GoldPrice.karat == item_in.karat, GoldPrice.is_current == True).first()
    rate = gp.price_per_gram if gp else Decimal("3420.00")
    metal_val = round_money(net_gold * rate)
    making_val = item_in.making_charge_rate if item_in.making_charge_type == "FLAT" else round_money(gross * item_in.making_charge_rate)
    retail_price = metal_val + making_val

    product = Product(
        sku=item_in.sku.strip(),
        barcode=item_in.barcode or item_in.sku.strip(),
        name=item_in.name.strip(),
        name_ar=item_in.name_ar.strip(),
        category_id=item_in.category_id,
        karat=item_in.karat,
        purity_pct=purity_pct,
        gross_weight=gross,
        stone_tare=tare,
        net_gold_weight=net_gold,
        making_charge_type=item_in.making_charge_type,
        making_charge_rate=item_in.making_charge_rate,
        retail_price=retail_price,
        cost_price=item_in.cost_price,
        quantity=item_in.quantity,
        min_stock_alert=item_in.min_stock_alert,
        image_url=item_in.image_url,
        hallmark_code=item_in.hallmark_code or f"{item_in.karat} • CAIRO ASSAY",
        status="IN_STOCK",
        is_archived=False,
        updated_by=admin.id
    )
    db.add(product)

    audit = AuditLog(
        user_id=admin.id,
        action="PRODUCT_CREATED",
        entity="Product",
        entity_id=product.id,
        details=f"Admin created product {product.name} ({product.sku}), Karat: {product.karat}, Net: {net_gold}g",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(product)
    return product

@router.put("/products/{product_id}", response_model=ProductResponse)
def admin_update_product(
    product_id: str,
    item_in: ProductAdminUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    changes = []
    if item_in.name is not None:
        product.name = item_in.name.strip()
        changes.append("name")
    if item_in.name_ar is not None:
        product.name_ar = item_in.name_ar.strip()
        changes.append("name_ar")
    if item_in.karat is not None:
        product.karat = item_in.karat
        product.purity_pct = round_money(KARAT_PURITY_RATIOS.get(item_in.karat, Decimal("0.875")) * Decimal("100"))
        changes.append("karat")
    if item_in.gross_weight is not None:
        product.gross_weight = item_in.gross_weight
        changes.append("gross_weight")
    if item_in.stone_tare is not None:
        product.stone_tare = item_in.stone_tare
        changes.append("stone_tare")

    # Validate weight relationship
    if product.stone_tare > product.gross_weight:
        raise HTTPException(status_code=400, detail="Stone tare weight cannot exceed gross weight.")
    product.net_gold_weight = round_weight(product.gross_weight - product.stone_tare)

    if item_in.making_charge_type is not None:
        product.making_charge_type = item_in.making_charge_type
        changes.append("making_charge_type")
    if item_in.making_charge_rate is not None:
        product.making_charge_rate = item_in.making_charge_rate
        changes.append("making_charge_rate")
    if item_in.cost_price is not None:
        product.cost_price = item_in.cost_price
        changes.append("cost_price")
    if item_in.quantity is not None:
        product.quantity = item_in.quantity
        changes.append("quantity")
    if item_in.min_stock_alert is not None:
        product.min_stock_alert = item_in.min_stock_alert
        changes.append("min_stock_alert")
    if item_in.status is not None:
        product.status = item_in.status
        changes.append("status")
    if item_in.hallmark_code is not None:
        product.hallmark_code = item_in.hallmark_code
    if item_in.image_url is not None:
        product.image_url = item_in.image_url

    # Recalculate retail valuation
    gp = db.query(GoldPrice).filter(GoldPrice.karat == product.karat, GoldPrice.is_current == True).first()
    rate = gp.price_per_gram if gp else Decimal("3420.00")
    metal_val = round_money(product.net_gold_weight * rate)
    making_val = product.making_charge_rate if product.making_charge_type == "FLAT" else round_money(product.gross_weight * product.making_charge_rate)
    product.retail_price = metal_val + making_val

    product.updated_at = datetime.now(timezone.utc)
    product.updated_by = admin.id

    audit = AuditLog(
        user_id=admin.id,
        action="PRODUCT_UPDATED",
        entity="Product",
        entity_id=product.id,
        details=f"Admin updated product {product.sku} fields: {', '.join(changes)}",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(product)
    return product

@router.post("/products/{product_id}/archive", response_model=ProductResponse)
def admin_archive_product(
    product_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_archived = True
    product.archived_at = datetime.now(timezone.utc)
    product.status = "ARCHIVED"
    product.updated_by = admin.id

    audit = AuditLog(
        user_id=admin.id,
        action="PRODUCT_ARCHIVED",
        entity="Product",
        entity_id=product.id,
        details=f"Admin soft-archived product {product.name} ({product.sku}). Historical sales preserved.",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(product)
    return product

@router.post("/products/{product_id}/unarchive", response_model=ProductResponse)
def admin_unarchive_product(
    product_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_archived = False
    product.archived_at = None
    product.status = "IN_STOCK"
    product.updated_by = admin.id

    audit = AuditLog(
        user_id=admin.id,
        action="PRODUCT_RESTORED",
        entity="Product",
        entity_id=product.id,
        details=f"Admin restored archived product {product.name} ({product.sku}) to IN_STOCK.",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{product_id}")
def admin_delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Destructive deletion is safely blocked if product has historical sales!
    Admin must use soft-archival to preserve tax and accounting invoices.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Safety check: references in SaleItem
    sales_count = db.query(SaleItem).filter(SaleItem.product_id == product_id).count()
    if sales_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Destructive deletion rejected: Product '{product.sku}' is referenced by {sales_count} historical invoice line(s). Use Archive instead to maintain statutory ETA ledger compliance."
        )

    sku = product.sku
    db.delete(product)

    audit = AuditLog(
        user_id=admin.id,
        action="PRODUCT_DELETED_PERMANENTLY",
        entity="Product",
        entity_id=product_id,
        details=f"Admin permanently deleted unreferenced product {sku}",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    return {"message": f"Product '{sku}' permanently deleted.", "id": product_id}

@router.get("/products/{product_id}/history")
def get_product_sales_history(
    product_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    items = db.query(SaleItem).filter(SaleItem.product_id == product_id).all()
    history = []
    for it in items:
        sale = it.sale
        history.append({
            "sale_id": sale.id,
            "invoice_number": sale.invoice_number,
            "sale_date": sale.created_at,
            "gross_weight": float(it.gross_weight),
            "net_gold_weight": float(it.net_gold_weight),
            "rate_snapshot": float(it.gold_rate_snapshot),
            "making_snapshot": float(it.making_charge_snapshot),
            "item_total": float(it.item_total),
            "cashier": sale.cashier.full_name if sale.cashier else "Unknown",
            "customer": sale.customer.full_name if sale.customer else "Walk-in Client"
        })
    return {
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "total_units_sold": len(history),
        "history": history
    }


# ==============================================================================
# SECTION 3: Employee Management & Staff Accounts
# ==============================================================================
@router.get("/employees", response_model=List[UserResponse])
def list_employees(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    res = []
    for u in users:
        perms = []
        try:
            if u.permissions:
                perms = json.loads(u.permissions)
        except Exception:
            perms = []
        res.append(UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            pin_configured=bool(u.pin_hash),
            permissions=perms,
            temp_password_active=bool(u.temp_password_active),
            last_login_at=u.last_login_at,
            created_at=u.created_at
        ))
    return res

@router.post("/employees", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    clean_email = payload.email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    # Generate secure password if none provided
    raw_password = payload.password or "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(12))
    pin_hash = get_pin_hash(payload.pin) if payload.pin else None

    # Safe default permissions for employee if not specified
    assigned_perms = payload.permissions or ["view_products", "view_stock", "record_sales", "view_sales_history", "view_gold_prices"]

    new_user = User(
        email=clean_email,
        full_name=payload.full_name.strip(),
        hashed_password=get_password_hash(raw_password),
        role=payload.role if payload.role in ["ADMIN", "EMPLOYEE"] else "EMPLOYEE",
        pin_hash=pin_hash,
        permissions=json.dumps(assigned_perms),
        temp_password_active=True if not payload.password else False,
        token_version=1,
        is_active=True
    )
    db.add(new_user)

    audit = AuditLog(
        user_id=admin.id,
        action="EMPLOYEE_CREATED",
        entity="User",
        details=f"Admin created employee {new_user.full_name} ({new_user.email}) with role {new_user.role}",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        pin_configured=bool(new_user.pin_hash),
        permissions=assigned_perms,
        temp_password_active=bool(new_user.temp_password_active),
        last_login_at=None,
        created_at=new_user.created_at
    )

@router.put("/employees/{user_id}", response_model=UserResponse)
def update_employee(
    user_id: str,
    payload: EmployeeUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Employee not found")

    changes = []
    if payload.full_name is not None:
        target.full_name = payload.full_name.strip()
        changes.append("full_name")
    if payload.email is not None and payload.email.lower() != target.email:
        clean_email = payload.email.strip().lower()
        exists = db.query(User).filter(User.email == clean_email).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email is already used by another account.")
        target.email = clean_email
        changes.append("email")

    if payload.role is not None and payload.role != target.role:
        # Safeguard: prevent demoting last active admin
        if target.role == "ADMIN" and payload.role != "ADMIN":
            active_admins = db.query(User).filter(User.role == "ADMIN", User.is_active == True).count()
            if active_admins <= 1:
                raise HTTPException(status_code=400, detail="Cannot demote the last remaining active Administrator.")
        target.role = payload.role
        changes.append(f"role->{payload.role}")

    if payload.permissions is not None:
        target.permissions = json.dumps(payload.permissions)
        changes.append("permissions")

    if payload.is_active is not None and payload.is_active != target.is_active:
        if target.role == "ADMIN" and payload.is_active is False:
            active_admins = db.query(User).filter(User.role == "ADMIN", User.is_active == True).count()
            if active_admins <= 1:
                raise HTTPException(status_code=400, detail="Cannot deactivate the last remaining active Administrator.")
        target.is_active = payload.is_active
        changes.append(f"is_active->{payload.is_active}")

    # Role/permission changes immediately revoke sessions
    target.token_version = (target.token_version or 1) + 1

    audit = AuditLog(
        user_id=admin.id,
        action="EMPLOYEE_UPDATED",
        entity="User",
        entity_id=target.id,
        details=f"Admin updated {target.email}: {', '.join(changes)}. Sessions revoked.",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(target)

    perms = []
    try:
        perms = json.loads(target.permissions) if target.permissions else []
    except Exception:
        pass

    return UserResponse(
        id=target.id,
        email=target.email,
        full_name=target.full_name,
        role=target.role,
        is_active=target.is_active,
        pin_configured=bool(target.pin_hash),
        permissions=perms,
        temp_password_active=bool(target.temp_password_active),
        last_login_at=target.last_login_at,
        created_at=target.created_at
    )

@router.post("/employees/{user_id}/toggle-status", response_model=UserResponse)
def toggle_employee_status(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Employee not found")

    new_status = not target.is_active

    # Safeguard: cannot deactivate last admin
    if target.role == "ADMIN" and not new_status:
        active_admins = db.query(User).filter(User.role == "ADMIN", User.is_active == True).count()
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="Security Safeguard: Cannot deactivate the last remaining active Administrator.")

    target.is_active = new_status
    target.token_version = (target.token_version or 1) + 1  # Revoke sessions

    action_label = "ACTIVATED" if new_status else "DEACTIVATED"
    audit = AuditLog(
        user_id=admin.id,
        action=f"EMPLOYEE_{action_label}",
        entity="User",
        entity_id=target.id,
        details=f"Admin {action_label.lower()} account {target.email}. Active sessions revoked.",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(target)

    perms = json.loads(target.permissions) if target.permissions else []
    return UserResponse(
        id=target.id,
        email=target.email,
        full_name=target.full_name,
        role=target.role,
        is_active=target.is_active,
        pin_configured=bool(target.pin_hash),
        permissions=perms,
        temp_password_active=bool(target.temp_password_active),
        last_login_at=target.last_login_at,
        created_at=target.created_at
    )

@router.delete("/employees/{user_id}")
def delete_employee(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Safeguard: cannot delete last active admin
    if target.role == "ADMIN":
        active_admins = db.query(User).filter(User.role == "ADMIN", User.is_active == True).count()
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="Security Safeguard: Cannot delete the last active Administrator.")

    # Check sales history
    sales_count = db.query(Sale).filter(Sale.cashier_id == user_id).count()
    if sales_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Destructive deletion rejected: Employee has processed {sales_count} sales transactions. Please deactivate the account instead to maintain financial audit integrity."
        )

    email = target.email
    db.delete(target)

    audit = AuditLog(
        user_id=admin.id,
        action="EMPLOYEE_DELETED",
        entity="User",
        entity_id=user_id,
        details=f"Admin permanently deleted employee account {email}",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    return {"message": f"Employee {email} deleted successfully.", "id": user_id}

@router.post("/employees/{user_id}/revoke-sessions")
def revoke_employee_sessions(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Employee not found")

    target.token_version = (target.token_version or 1) + 1
    audit = AuditLog(
        user_id=admin.id,
        action="SESSIONS_REVOKED",
        entity="User",
        entity_id=target.id,
        details=f"Admin revoked all active login tokens for {target.email}",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    return {"message": f"All active sessions for {target.email} have been revoked immediately."}


# ==============================================================================
# SECTION 4: Roles & Permissions
# ==============================================================================
@router.get("/permissions")
def get_available_permissions(
    admin: User = Depends(require_admin)
):
    return {"permissions": AVAILABLE_PERMISSIONS}

@router.put("/employees/{user_id}/permissions")
def update_employee_permissions(
    user_id: str,
    permissions: List[str],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Employee not found")

    target.permissions = json.dumps(permissions)
    target.token_version = (target.token_version or 1) + 1  # Invalidate current session to apply new permissions

    audit = AuditLog(
        user_id=admin.id,
        action="PERMISSIONS_UPDATED",
        entity="User",
        entity_id=target.id,
        details=f"Admin modified permissions for {target.email}: {permissions}",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    return {"message": f"Permissions updated for {target.email}.", "permissions": permissions}


# ==============================================================================
# SECTION 5: Login Credentials & PIN Management
# ==============================================================================
@router.post("/employees/{user_id}/reset-password")
def reset_employee_password(
    user_id: str,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Generate secure temporary password if not provided
    temp_pass = payload.new_password or ("Tmp#" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8)) + "!")
    target.hashed_password = get_password_hash(temp_pass)
    target.temp_password_active = True
    target.token_version = (target.token_version or 1) + 1  # Invalidate all active sessions

    audit = AuditLog(
        user_id=admin.id,
        action="PASSWORD_RESET_ISSUED",
        entity="User",
        entity_id=target.id,
        details=f"Admin issued temporary password reset for {target.email}. Temporary flag active.",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Password reset for {target.email}. Temporary credentials issued.",
        "temporary_password": temp_pass,
        "requires_change_on_first_login": True
    }

@router.post("/employees/{user_id}/reset-pin")
def reset_employee_pin(
    user_id: str,
    payload: PinResetRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Generate 4-digit PIN if not provided
    generated_pin = payload.pin or f"{secrets.randbelow(9000) + 1000}"
    target.pin_hash = get_pin_hash(generated_pin)
    target.failed_pin_attempts = 0
    target.pin_locked_until = None
    target.token_version = (target.token_version or 1) + 1  # Invalidate active sessions

    audit = AuditLog(
        user_id=admin.id,
        action="PIN_RESET_ISSUED",
        entity="User",
        entity_id=target.id,
        details=f"Admin updated security PIN for {target.email}. Lockout cleared.",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"PIN for {target.email} has been reset.",
        "issued_pin": generated_pin,
        "note": "Secure salted PBKDF2 hash stored. Plaintext PIN will not be displayed again."
    }


# ==============================================================================
# SECTION 6: API Key Management (Gold Price Provider)
# ==============================================================================
@router.get("/api-keys", response_model=List[ApiKeyConfigResponse])
def get_api_key_configs(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    configs = db.query(ApiKeyConfig).order_by(ApiKeyConfig.created_at.desc()).all()
    if not configs:
        # Provide default Daleelak configuration
        default_config = ApiKeyConfig(
            provider_name="getdaleelak.com",
            endpoint_url="https://getdaleelak.com/api/v1/feed.json",
            masked_key="PUBLIC-FREE-ACCESS",
            is_active=True,
            validation_status="VALID",
            last_tested_at=datetime.now(timezone.utc),
            last_success_at=datetime.now(timezone.utc)
        )
        db.add(default_config)
        db.commit()
        db.refresh(default_config)
        configs = [default_config]

    return configs

@router.post("/api-keys/test")
async def test_api_key_connection(
    payload: ApiKeyTestRequest,
    admin: User = Depends(require_admin)
):
    """
    Safe test request against external gold price provider before activating key.
    """
    headers = {
        "Accept": "application/json",
        "User-Agent": "3M-Dahab-JewelryOS/1.0 (Admin Key Validation Test)"
    }
    if payload.api_key:
        headers["Authorization"] = f"Bearer {payload.api_key.strip()}"

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(payload.endpoint_url.strip(), headers=headers)
            if resp.status_code in [200, 304]:
                return {
                    "valid": True,
                    "status_code": resp.status_code,
                    "message": f"Connection verified successfully with {payload.provider_name}.",
                    "response_preview": "Verified 200 OK Market Feed JSON"
                }
            else:
                return {
                    "valid": False,
                    "status_code": resp.status_code,
                    "message": f"Provider responded with HTTP status {resp.status_code}.",
                    "error": resp.text[:200]
                }
    except Exception as e:
        return {
            "valid": False,
            "status_code": 0,
            "message": f"Network error contacting {payload.endpoint_url}: {str(e)}",
            "error": str(e)
        }

@router.post("/api-keys", response_model=ApiKeyConfigResponse)
async def configure_api_key(
    payload: ApiKeyUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Replaces or updates API key with mandatory pre-validation test.
    If validation fails, the existing working configuration is strictly preserved!
    """
    # 1. Test key first
    test_result = await test_api_key_connection(ApiKeyTestRequest(
        provider_name=payload.provider_name,
        endpoint_url=payload.endpoint_url,
        api_key=payload.api_key
    ), admin=admin)

    if not test_result["valid"]:
        audit = AuditLog(
            user_id=admin.id,
            action="API_KEY_VALIDATION_FAILED",
            entity="ApiKeyConfig",
            details=f"Validation failed for {payload.provider_name}: {test_result['message']}. Working key preserved.",
            outcome="FAILED"
        )
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"API Key validation failed ({test_result['message']}). Existing working configuration was preserved."
        )

    # 2. Deactivate previous configs
    db.query(ApiKeyConfig).update({"is_active": False})

    # 3. Store protected secret and mask
    masked = mask_secret(payload.api_key) if payload.api_key else "PUBLIC-FREE-ACCESS"
    new_config = ApiKeyConfig(
        provider_name=payload.provider_name.strip(),
        endpoint_url=payload.endpoint_url.strip(),
        api_key_encrypted=payload.api_key.strip() if payload.api_key else None,
        masked_key=masked,
        is_active=True,
        last_tested_at=datetime.now(timezone.utc),
        last_success_at=datetime.now(timezone.utc),
        validation_status="VALID",
        last_error_message=None,
        updated_by=admin.id
    )
    db.add(new_config)

    audit = AuditLog(
        user_id=admin.id,
        action="API_KEY_ROTATED",
        entity="ApiKeyConfig",
        details=f"Admin activated validated API key for {payload.provider_name} ({masked})",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(new_config)
    return new_config

@router.post("/api-keys/{config_id}/revoke")
def revoke_api_key(
    config_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    config = db.query(ApiKeyConfig).filter(ApiKeyConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="API key config not found")

    config.is_active = False
    config.validation_status = "REVOKED"
    audit = AuditLog(
        user_id=admin.id,
        action="API_KEY_REVOKED",
        entity="ApiKeyConfig",
        entity_id=config.id,
        details=f"Admin revoked API key configuration for {config.provider_name}",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    return {"message": f"API key for {config.provider_name} has been revoked."}


# ==============================================================================
# SECTION 7: Software License Key Management
# ==============================================================================
@router.get("/license", response_model=LicenseStatusResponse)
def get_license_status(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return LicenseService.get_license_status(db)

@router.post("/license/activate", response_model=LicenseStatusResponse)
def activate_license(
    payload: LicenseActivateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    try:
        return LicenseService.activate_license(db, payload.license_key, payload.licensed_to, admin)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/license/deactivate", response_model=LicenseStatusResponse)
def deactivate_license(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return LicenseService.deactivate_license(db, admin)


# ==============================================================================
# SECTION 8: Security & Audit Logs
# ==============================================================================
@router.get("/audit-logs", response_model=List[AuditLogItemResponse])
def get_audit_logs(
    action: Optional[str] = None,
    entity: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    query = db.query(AuditLog)
    if action and action != "ALL":
        query = query.filter(AuditLog.action == action)
    if entity and entity != "ALL":
        query = query.filter(AuditLog.entity == entity)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    res = []
    for l in logs:
        u_name = l.user.full_name if l.user else "System Automation"
        u_email = l.user.email if l.user else None
        res.append(AuditLogItemResponse(
            id=l.id,
            timestamp=l.created_at,
            user_name=u_name,
            user_email=u_email,
            action=l.action,
            entity=l.entity,
            entity_id=l.entity_id,
            details=l.details,
            outcome=getattr(l, "outcome", "SUCCESS"),
            safe_metadata=getattr(l, "safe_metadata", None)
        ))
    return res


# ==============================================================================
# SECTION 9: System Settings Repository
# ==============================================================================
@router.get("/settings", response_model=List[SystemSettingResponse])
def get_system_settings(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    settings_list = db.query(SystemSetting).all()
    if not settings_list:
        defaults = [
            ("eta_vat_making_pct", "14.0", "Egyptian ETA VAT percentage applied exclusively to workmanship (Law #67/2016)"),
            ("max_cashier_discount_pct", "5.0", "Maximum discount cashier can apply without manager authorization"),
            ("enforce_laser_hallmark", "true", "Require official Laser Hallmark QR Code on tax invoices"),
            ("session_idle_timeout_min", "60", "POS workstation auto-lock idle timeout in minutes"),
            ("allow_scrap_tradein_without_id", "false", "Require national ID for customer scrap gold buy-backs over 5,000 EGP")
        ]
        for k, v, d in defaults:
            db.add(SystemSetting(setting_key=k, setting_value=v, description=d))
        db.commit()
        settings_list = db.query(SystemSetting).all()

    return [
        SystemSettingResponse(
            key=s.setting_key,
            value=s.setting_value,
            description=s.description,
            updated_at=s.updated_at
        )
        for s in settings_list
    ]

@router.put("/settings")
def update_system_settings(
    payload: SystemSettingsUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    updated = []
    for k, v in payload.settings.items():
        s = db.query(SystemSetting).filter(SystemSetting.setting_key == k).first()
        if s:
            s.setting_value = str(v)
            s.updated_at = datetime.now(timezone.utc)
            s.updated_by = admin.id
            updated.append(k)
        else:
            new_s = SystemSetting(
                setting_key=k,
                setting_value=str(v),
                updated_at=datetime.now(timezone.utc),
                updated_by=admin.id
            )
            db.add(new_s)
            updated.append(k)

    audit = AuditLog(
        user_id=admin.id,
        action="SYSTEM_SETTINGS_UPDATED",
        entity="SystemSetting",
        details=f"Admin updated system settings: {', '.join(updated)}",
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    return {"message": "System settings saved successfully.", "updated_keys": updated}
