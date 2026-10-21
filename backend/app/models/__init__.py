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
    status = Column(String(30), default="IN_STOCK", index=True) # "IN_STOCK", "RESERVED", "SOLD", "WORKSHOP"
    is_unique = Column(Boolean, default=True)
    quantity = Column(Integer, default=1)
    image_url = Column(String(500), nullable=True)
    hallmark_code = Column(String(100), nullable=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")
