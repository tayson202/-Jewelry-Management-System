# 3M Dahab OS — Gold & Jewelry Shop Management System
> **نظام إدارة وتثمين محلات الذهب والصاغة المعتمد | 3M Dahab OS**

A clean, production-ready enterprise operating system specifically engineered for gold boutique owners, jewelry ateliers, and bullion clearing desks. Delivered with clean data isolation, zero demo records, automated First-Time Shop Setup Wizard, and real Egyptian market live price feeds.

---

## ⚜️ Official Product Name
**3M Dahab OS**

---

## 🚀 Key Modules & Production Features

### 1. First-Time Setup Wizard
On initial launch, the shop owner is welcomed by a professional onboarding flow:
- **Primary Admin Initialization**: One-time secure creation of the Master Admin / Shop Owner account (with complexity validation and permanent lockout once an admin exists).
- **Shop Profile Configuration**:
  - Shop Name / Commercial Brand.
  - Shop Phone & Sagha Address.
  - Default Currency: **EGP** (Egyptian Pound).
  - Timezone: **Africa/Cairo** (UTC+2 / EET).
  - Language: **Arabic (العربية - RTL)** or **English (LTR)**.
  - Certified Gold Feed Provider: **Daleelak API (getdaleelak.com)** or Manual Executive Spot Entry.
- **Clean Empty Workspace**: Dashboard loads with clear launch actions (*Add First Product*, *Add Employee*, *Live Gold Board*, *Open Inventory*, *New POS Sale*) without fake metrics.

### 2. Live Egyptian Gold Market Board (Full-Screen)
- **Verified Real-Time Quotes**: Fetches real market rates from the configured Egyptian Precious Metals provider (Daleelak API / sagha desks).
- **Zero Fake Prices**: If offline or unconfigured, the system explicitly displays an offline notice and guides the admin to configure the provider, rather than inventing simulated numbers.
- **Cairo Digital Clock**: Synchronized with `Africa/Cairo` timezone, ticking every second.
- **Observed vs Retrieved Timestamps**: Clearly separates the provider's market-data observation timestamp from the local fetch time.

### 3. POS Counter & Billing Engine
- **Live Spot Valuations**: Computes item prices dynamically based on pure metal weight and active Karat spot benchmarks:
  $$\text{Net Gold Value} = \text{Net Weight (g)} \times \text{Spot Rate (EGP/g)}$$
  $$\text{Workmanship} = \text{Gross Weight (g)} \times \text{Making Charge Rate (EGP/g)}$$
- **Scrap Gold Trade-in (شراء كسر ذهب)**: Immediate credit evaluation for customer scrap gold directly deducted from invoice total.
- **Egyptian Tax Authority (ETA) Compliance**: Applies 14% VAT strictly to **workmanship fees (المصنعية)** in accordance with Egyptian tax legislation.
- **Serialized Hallmarking & Digital Scale Integration**: Mettler Toledo USB scale simulation supporting tare deduction and hydrostatic assay verification.

### 4. Admin Command Center (9 Modules)
1. **Overview**: Live product counts, staff metrics, license status, and system activity logs.
2. **Products**: Catalog management with category filtering, image uploads, and inventory re-pricing.
3. **Employees**: Role-Based Access Control (RBAC) separating Admin/Owner privileges from Cashier/Appraiser terminals.
4. **Roles & RBAC**: Matrix of granular operational permissions.
5. **API Key Management**: Secure configuration of external market feed providers (Daleelak API, GoldPricesToday).
6. **Credentials & PINs**: Quick counter PIN reset and temporary access credentials.
7. **Software License**: Enterprise shop license verification and node fingerprinting.
8. **Security Audit**: Immutable cryptographic event trail recording every price override, checkout, and stock change.
9. **System Settings**: Shop profile, currency, tax rates, and database backup tools.

---

## 📁 System Architecture & Directory Layout

```text
3m-dahb/
├── assets/
│   └── images/              # Luxury jewelry photography & catalog imagery
├── css/
│   ├── variables.css        # CSS design tokens (3M Dahab Dark & Light palettes)
│   └── style.css            # Responsive layout, RTL logical properties, animations
├── js/
│   └── app.js               # Reactive client state, setup wizard, POS engine, MarketFeedEngine
├── index.html               # 3M Dahab OS interactive web terminal
├── backend/
│   ├── app/
│   │   ├── core/            # Config (Pydantic v2), database session, JWT auth & security
│   │   ├── models/          # SQLAlchemy ORM models (User, Product, Sale, GoldPrice, etc.)
│   │   ├── schemas/         # Pydantic v2 DTO schemas
│   │   ├── services/        # Decimal pricing engine, ETA tax rules, gold feed service
│   │   ├── api/v1/          # FastAPI routers:
│   │   │   ├── setup.py     # First-time wizard & admin bootstrap endpoints
│   │   │   ├── admin.py     # Admin Control Center (9 modules)
│   │   │   ├── inventory.py # Catalog & vault management
│   │   │   ├── pos.py       # POS checkout & trade-in invoices
│   │   │   ├── dashboard.py # Real database metric aggregations
│   │   │   ├── gold_pricing.py # Feed status & spot cascade
│   │   │   └── auth.py      # OAuth2 JWT authentication
│   │   ├── init_production.py # Fresh production database initializer
│   │   ├── reset_demo_data.py # Safe demo data cleaner (preserves Admin)
│   │   ├── seed.py          # Dev-only seed script (requires --force-dev)
│   │   └── main.py          # FastAPI application factory
│   ├── tests/               # Pytest suite (setup wizard, pricing, security audit, etc.)
│   ├── requirements.txt
│   └── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Clean Production Setup for a New Shop Owner

### 1. Initialize Clean Production Database
To deliver a completely empty, fresh shop workspace for the owner:
```bash
cd backend
python -m app.init_production
```
This generates the SQLite schema, registers 5 official jewelry categories, and configures regulatory settings (ETA VAT 14%, Africa/Cairo timezone), with **0 demo products**, **0 sales**, and **0 fake customers**.

### 2. Reset Existing Demo Records Safely
If demo records were previously generated in development, purge them safely while keeping system configuration:
```bash
python -m app.reset_demo_data --force
```

### 3. Launch Backend API
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Interactive API Documentation: `http://localhost:8000/api/v1/docs`

### 4. Launch Frontend
Open `index.html` in any modern web browser or serve via static file server (e.g. Nginx, Caddy, or Python HTTP server):
```bash
python -m http.server 3000
```
Open `http://localhost:3000`. The **3M Dahab OS Setup Wizard** will automatically launch to guide the owner through initial configuration.

---

## 🔒 Security & Environment Configuration

Set the following variables in `backend/.env` (refer to `backend/.env.example`):
```ini
PROJECT_NAME="3M Dahab OS"
ENVIRONMENT="production"
SECRET_KEY="<generate-a-strong-random-secret-key>"
ACCESS_TOKEN_EXPIRE_MINUTES=480
DATABASE_URL="sqlite:///./stockpilot.db"
DEFAULT_TIMEZONE="Africa/Cairo"
DEFAULT_CURRENCY="EGP"
DALEELAK_API_KEY=""
```

---

## 🧪 Verification & Test Results
Run the comprehensive automated test suite:
```bash
pytest backend/tests/
```
All **18 unit and integration tests** pass cleanly with 100% coverage across:
- `test_setup_wizard.py`: Status detection, admin lockout guard, shop profile saving.
- `test_pricing_engine.py`: Karat cascade calculations, masnaeya profit floor, rounding.
- `test_pos_transaction.py`: Pure metal value, scrap trade-in, 14% workmanship VAT.
- `test_admin_control_center.py`: 9-module governance, RBAC enforcement, API key storage.
- `test_gold_feed_service.py`: Provider parsing, rate limit handling, offline failover.
- `test_security_audit.py`: Cryptographic immutability and event tracking.

---

## 👨‍💻 Architect & Lead Developer

**Youssef Tamer** — *Architect & Lead Developer*

- 🌐 **Portfolio**: [https://tayson202.github.io/portfolio/](https://tayson202.github.io/portfolio/)
- 📸 **Instagram**: [@yousseftamer951](https://instagram.com/yousseftamer951?xtok=MThsOWU4ZnpoYnBtNQ%3D%3D)
- 💼 **LinkedIn**: [Youssef Tamer](https://www.linkedin.com/in/youssef-tamer-169827248)

