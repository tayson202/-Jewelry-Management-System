import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="EMPLOYEE", nullable=False)  # "ADMIN" or "EMPLOYEE"
    is_active = Column(Boolean, default=True)
    pin_hash = Column(String(255), nullable=True)  # Salted PBKDF2 hash of 4-6 digit employee PIN
    failed_pin_attempts = Column(Integer, default=0)
    pin_locked_until = Column(DateTime, nullable=True)
    permissions = Column(Text, default="[]")  # JSON string array of granular permissions
    temp_password_active = Column(Boolean, default=False)  # Requires reset on next login
    token_version = Column(Integer, default=1)  # Incremented to immediately revoke sessions
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sales = relationship("Sale", back_populates="cashier")
    audit_logs = relationship("AuditLog", back_populates="user")


class GoldPrice(Base):
    __tablename__ = "gold_prices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    karat = Column(String(10), index=True, nullable=False)  # '24K', '22K', '21K', '18K', '14K'
    purity_pct = Column(Numeric(6, 3), nullable=False)     # e.g. 100.00, 91.67, 87.50, 75.00, 58.33
    price_per_gram = Column(Numeric(12, 2), nullable=False)
    spread_sell = Column(Numeric(10, 2), default=0.00)
    spread_buy = Column(Numeric(10, 2), default=0.00)
    source = Column(String(100), default="SAGHA_DESK")
    is_current = Column(Boolean, default=True)
    effective_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    default_making_charge = Column(Numeric(10, 2), default=150.00)
    floor_margin_pct = Column(Numeric(5, 2), default=10.00)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    barcode = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=False)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    karat = Column(String(10), nullable=False)             # '24K', '22K', '21K', '18K', '14K'
    purity_pct = Column(Numeric(6, 3), nullable=False)
    gross_weight = Column(Numeric(10, 3), nullable=False)  # in grams
    stone_tare = Column(Numeric(10, 3), default=0.000)     # in grams
    net_gold_weight = Column(Numeric(10, 3), nullable=False) # gross - stone_tare
    making_charge_type = Column(String(20), default="PER_GRAM") # "PER_GRAM" or "FLAT"
    making_charge_rate = Column(Numeric(10, 2), nullable=False)
    retail_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), default=0.00)
    status = Column(String(30), default="IN_STOCK", index=True) # "IN_STOCK", "RESERVED", "SOLD", "WORKSHOP", "ARCHIVED"
    is_archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    is_unique = Column(Boolean, default=True)
    quantity = Column(Integer, default=1)
    min_stock_alert = Column(Integer, default=1)
    image_url = Column(String(500), nullable=True)
    hallmark_code = Column(String(100), nullable=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    vip_tier = Column(String(50), default="Standard")  # "VIP Tier 1", "Gold", "Standard"
    loyalty_points = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sales = relationship("Sale", back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    balance_egp = Column(Numeric(14, 2), default=0.00)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    products = relationship("Product", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    cashier_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True)
    
    total_net_gold_weight = Column(Numeric(10, 3), nullable=False)
    metal_base_value = Column(Numeric(12, 2), nullable=False)
    total_making_charges = Column(Numeric(12, 2), nullable=False)
    gross_goods_subtotal = Column(Numeric(12, 2), nullable=False)
    scrap_credit_deducted = Column(Numeric(12, 2), default=0.00)
    statutory_vat = Column(Numeric(10, 2), default=0.00)  # 14% on Making Charges Only
    discount_amount = Column(Numeric(10, 2), default=0.00)
    net_payable_total = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), default="CASH")   # "CASH", "POS_TERMINAL", "SPLIT"
    status = Column(String(30), default="COMPLETED")      # "COMPLETED", "REFUNDED", "CANCELLED"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    cashier = relationship("User", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    trade_ins = relationship("TradeInItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sale_id = Column(String(36), ForeignKey("sales.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    karat = Column(String(10), nullable=False)
    gross_weight = Column(Numeric(10, 3), nullable=False)
    net_gold_weight = Column(Numeric(10, 3), nullable=False)
    gold_rate_snapshot = Column(Numeric(12, 2), nullable=False)
    making_charge_snapshot = Column(Numeric(10, 2), nullable=False)
    item_total = Column(Numeric(12, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


class TradeInItem(Base):
    __tablename__ = "trade_in_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sale_id = Column(String(36), ForeignKey("sales.id"), nullable=False)
    description = Column(String(255), default="Customer Scrap Gold Trade-in")
    karat = Column(String(10), nullable=False)
    gross_weight = Column(Numeric(10, 3), nullable=False)
    applied_rate_per_g = Column(Numeric(12, 2), nullable=False)
    total_credit = Column(Numeric(12, 2), nullable=False)

    sale = relationship("Sale", back_populates="trade_ins")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False)
    reference_no = Column(String(100), nullable=False)
    total_weight = Column(Numeric(10, 3), nullable=False)
    total_cost = Column(Numeric(14, 2), nullable=False)
    status = Column(String(30), default="COMPLETED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    supplier = relationship("Supplier", back_populates="purchases")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category = Column(String(100), nullable=False)  # "Rent", "Salaries", "Utilities", "Packaging"
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    outcome = Column(String(20), default="SUCCESS")  # "SUCCESS", "FAILED", "BLOCKED"
    ip_address = Column(String(50), nullable=True)
    safe_metadata = Column(Text, nullable=True)  # JSON-encoded safe context (no secrets)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")


class ApiKeyConfig(Base):
    """
    Secure server-side storage for external market feed API credentials.
    Full API keys are never leaked to frontend clients or client-visible state.
    """
    __tablename__ = "api_key_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider_name = Column(String(100), default="getdaleelak.com", nullable=False)  # "getdaleelak.com", "goldpricestoday.net", "custom"
    endpoint_url = Column(String(500), nullable=False)
    api_key_encrypted = Column(String(500), nullable=True)  # Protected server-side secret
    masked_key = Column(String(50), nullable=True)         # e.g. "••••••••AB12"
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    validation_status = Column(String(50), default="UNTESTED")  # "VALID", "FAILED", "UNTESTED"
    last_error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)


class LicenseConfig(Base):
    """
    Cryptographic license verification and status tracking.
    Never accepts arbitrary strings as valid licenses.
    """
    __tablename__ = "license_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    license_key_masked = Column(String(100), nullable=False)  # e.g. "AURUM-ENT-••••-F421"
    license_hash = Column(String(255), nullable=False)        # SHA-256 digest of original key
    license_type = Column(String(50), default="ENTERPRISE")    # "ENTERPRISE", "BOUTIQUE_SINGLE", "DEMO"
    licensed_to = Column(String(255), default="3M Dahab - Cairo Central Vault")
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="ACTIVE")             # "ACTIVE", "EXPIRED", "UNLICENSED", "REVOKED"
    allowed_features = Column(Text, default='["inventory", "pos", "gold_engine", "reports", "eta_tax", "admin_command"]')
    max_terminals = Column(Integer, default=5)
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    last_verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    signature = Column(String(500), nullable=True)            # Cryptographic signature
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemSetting(Base):
    """
    Dynamic server-side settings repository for ETA tax rates, discount caps, and security policies.
    """
    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    setting_key = Column(String(100), unique=True, index=True, nullable=False)
    setting_value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
