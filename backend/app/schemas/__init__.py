from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "EMPLOYEE"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Gold Pricing Schemas ---
class RecalibrateRequest(BaseModel):
    base_24k_rate: Decimal = Field(..., gt=0, description="Base 24K pure bullion rate in EGP per gram")

class GoldRateItem(BaseModel):
    karat: str
    purity_pct: float
    price_per_gram: float
    spread_sell: float
    buy_back: float

class GoldPricingResponse(BaseModel):
    base_24k_rate: float
    lbm_reference_usd: float = 2342.40
    currency: str = "EGP"
    updated_at: datetime
    rates: Dict[str, GoldRateItem]

# --- Product / Inventory Schemas ---
class ProductCreate(BaseModel):
    sku: str
    barcode: Optional[str] = None
    name: str
    name_ar: str
    category_id: Optional[str] = None
    karat: str  # '24K', '22K', '21K', '18K', '14K'
    gross_weight: Decimal = Field(..., gt=0)
    stone_tare: Decimal = Field(default=Decimal("0.000"), ge=0)
    making_charge_type: str = "PER_GRAM"  # "PER_GRAM" or "FLAT"
    making_charge_rate: Decimal = Field(..., ge=0)
    image_url: Optional[str] = None
    hallmark_code: Optional[str] = None
    is_unique: bool = True
    quantity: int = 1

class ProductResponse(BaseModel):
    id: str
    sku: str
    barcode: Optional[str] = None
    name: str
    name_ar: str
    category_id: Optional[str] = None
    karat: str
    purity_pct: float
    gross_weight: float
    stone_tare: float
    net_gold_weight: float
    making_charge_type: str
    making_charge_rate: float
    retail_price: float
    status: str
    is_unique: bool
    quantity: int
    image_url: Optional[str] = None
    hallmark_code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- POS & Sales Schemas ---
class POSCartItemInput(BaseModel):
    product_id: str
    karat: str
    gross_weight: float
    net_gold_weight: float
    gold_rate_snapshot: float
    making_charge_snapshot: float
    making_charge_type: str = "PER_GRAM"

class POSTradeInInput(BaseModel):
    description: str = "Customer Scrap Gold Trade-in"
    karat: str
    gross_weight: float
    applied_rate_per_g: float

class POSCalculateRequest(BaseModel):
    items: List[POSCartItemInput]
    trade_ins: List[POSTradeInInput] = []
    discount_amount: float = 0.0

class POSCheckoutRequest(BaseModel):
    items: List[POSCartItemInput]
    trade_ins: List[POSTradeInInput] = []
    customer_id: Optional[str] = None
    discount_amount: float = 0.0
    payment_method: str = "CASH"  # "CASH", "POS_TERMINAL", "SPLIT"

class SaleItemResponse(BaseModel):
    id: str
    product_id: str
    karat: str
    gross_weight: float
    net_gold_weight: float
    gold_rate_snapshot: float
    making_charge_snapshot: float
    item_total: float

    class Config:
        from_attributes = True

class SaleResponse(BaseModel):
    id: str
    invoice_number: str
    cashier_id: str
    customer_id: Optional[str]
    total_net_gold_weight: float
    metal_base_value: float
    total_making_charges: float
    gross_goods_subtotal: float
    scrap_credit_deducted: float
    statutory_vat: float
    discount_amount: float
    net_payable_total: float
    payment_method: str
    status: str
    created_at: datetime
    items: List[SaleItemResponse] = []

    class Config:
        from_attributes = True

# --- Dashboard Schemas ---
class DashboardMetricsResponse(BaseModel):
    vault_total_valuation: float
    total_vault_pure_weight: float
    todays_pos_sales: float
    todays_orders_count: int
    realized_margin: float
    active_atelier_pieces: int
    low_stock_count: int
