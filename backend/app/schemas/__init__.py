from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: Optional[str] = None
    temp_password_active: bool = False

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PinLoginRequest(BaseModel):
    email: EmailStr
    pin: str = Field(..., min_length=4, max_length=8)

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "EMPLOYEE"
    permissions: List[str] = []

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    pin_configured: bool = False
    permissions: List[str] = []
    temp_password_active: bool = False
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

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
    cost_price: float = 0.0
    status: str
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    is_unique: bool
    quantity: int
    min_stock_alert: int = 1
    image_url: Optional[str] = None
    hallmark_code: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

# --- Dashboard Schemas ---
class DashboardMetricsResponse(BaseModel):
    vault_total_valuation: float
    total_vault_pure_weight: float
    todays_pos_sales: float
    todays_orders_count: int
    realized_margin: float
    active_atelier_pieces: int
    low_stock_count: int

# --- Admin Control Center Schemas ---
class EmployeeCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: Optional[str] = None
    pin: Optional[str] = Field(None, min_length=4, max_length=8)
    role: str = "EMPLOYEE"
    permissions: List[str] = []

class EmployeeUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class PasswordResetRequest(BaseModel):
    new_password: Optional[str] = None

class PinResetRequest(BaseModel):
    pin: Optional[str] = Field(None, min_length=4, max_length=8)

class ProductAdminCreate(BaseModel):
    sku: str
    barcode: Optional[str] = None
    name: str
    name_ar: str
    category_id: Optional[str] = None
    karat: str
    gross_weight: Decimal = Field(..., gt=0)
    stone_tare: Decimal = Field(default=Decimal("0.000"), ge=0)
    making_charge_type: str = "PER_GRAM"
    making_charge_rate: Decimal = Field(..., ge=0)
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    quantity: int = Field(default=1, ge=0)
    min_stock_alert: int = Field(default=1, ge=0)
    image_url: Optional[str] = None
    hallmark_code: Optional[str] = None

class ProductAdminUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    karat: Optional[str] = None
    gross_weight: Optional[Decimal] = Field(None, gt=0)
    stone_tare: Optional[Decimal] = Field(None, ge=0)
    making_charge_type: Optional[str] = None
    making_charge_rate: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)
    min_stock_alert: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    hallmark_code: Optional[str] = None
    image_url: Optional[str] = None

class ApiKeyConfigResponse(BaseModel):
    id: str
    provider_name: str
    endpoint_url: str
    masked_key: Optional[str] = None
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    validation_status: str
    last_error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ApiKeyUpdateRequest(BaseModel):
    provider_name: str
    endpoint_url: str
    api_key: Optional[str] = None

class ApiKeyTestRequest(BaseModel):
    provider_name: str
    endpoint_url: str
    api_key: Optional[str] = None

class LicenseStatusResponse(BaseModel):
    is_configured: bool
    status: str
    license_type: str
    licensed_to: str
    masked_key: Optional[str] = None
    allowed_features: List[str] = []
    max_terminals: int = 5
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    notes: Optional[str] = None

class LicenseActivateRequest(BaseModel):
    license_key: str
    licensed_to: Optional[str] = None

class SystemSettingResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None

class SystemSettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]

class AuditLogItemResponse(BaseModel):
    id: str
    timestamp: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    entity: str
    entity_id: Optional[str] = None
    details: Optional[str] = None
    outcome: str = "SUCCESS"
    safe_metadata: Optional[str] = None

class AdminOverviewResponse(BaseModel):
    active_products: int
    archived_products: int
    low_stock_alerts: int
    active_employees: int
    total_employees: int
    license_summary: Dict[str, Any]
    api_connection_summary: Dict[str, Any]
    recent_audits: List[AuditLogItemResponse]

