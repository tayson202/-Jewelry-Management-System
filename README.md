# StockPilot (AURUM OS) — Gold & Jewelry Shop Management System
> **نظام إدارة وتثمين مجوهرات عم دهب (Maison D'Or)**

A complete, production-oriented web platform specifically engineered for luxury gold and jewelry retail, wholesale inventory vault management, dynamic bullion pricing, and point-of-sale invoicing.

---

## 🔗 Repository
- **Remote Origin**: [tayson202/-Jewelry-Management-System](https://github.com/tayson202/-Jewelry-Management-System.git)
- **Branch**: `main`

---

## 📸 Design Aesthetics & Visual Identity
The system faithfully implements both visual themes from the Figma designs:
1. **Dark Luxury Mode (AURUM OS / Haute Joaillerie)**: Deep obsidian/charcoal backdrop (`#0c0e12`), brushed champagne gold accents (`#d4af37`), and glassmorphism.
2. **Light Mode (StockPilot PRO / Maison D'Or)**: Clean warm off-white (`#f7f6f2`), muted gold borders, and high-readability financial typography.
3. **Bilingual Arabic & English**: Full toggle with native **RTL (Right-to-Left)** mirroring and Egyptian jewelry market terminology (عيار 21، المصنعية، كسر الذهب، تصفية الميزان، ضريبة القيمة المضافة 14% على المصنعية).

---

## 🚀 Key Modules & Capabilities

### 1. Gold Pricing Engine & Karat Cascade
- **Master 24K Pure Ingot Baseline**: Central Egyptian Bullion Clearinghouse (Sagha Desk) rate input (`EGP 3,420.00`).
- **Mathematical Karat Cascade**: Computes outright gram rates using exact ratios:
  - **24K**: 100.0% ($3,420.00 \text{ EGP/g}$)
  - **22K**: 91.67% ($3,135.00 \text{ EGP/g}$)
  - **21K Benchmark**: 87.50% ($2,992.50 \text{ EGP/g}$ — Egyptian Pivot)
  - **18K**: 75.00% ($2,565.00 \text{ EGP/g}$ — Italian Standard)
  - **14K**: 58.33% ($1,995.00 \text{ EGP/g}$ — Commercial)
- **Profit Floor Policy**: Enforces minimum making charge thresholds (Masnaeya) per category.

### 2. POS Counter & Billing
- **Live Cart Breakdown**:
  $$\text{Net Gold Value} = \text{Net Weight (g)} \times \text{Spot Rate}$$
  $$\text{Making Fee} = \text{Gross Weight (g)} \times \text{Making Charge Rate}$$
- **Scrap Gold Trade-in (شراء كسر ذهب)**: Deducts trade-in scrap gold credit directly from the customer invoice.
- **Egyptian Tax Authority (ETA) VAT**: Strictly calculates 14% sales tax on the **making charges only** (in accordance with Egyptian gold tax legislation).
- **Printable Luxury Invoice**: Generates official invoices with invoice number, customer tier, hallmarking details, and itemized breakdown.

### 3. Digital Vault Inventory
- Serialized unique pieces (e.g., *Aethelred Solitaire Royale*, *Vendôme Floral Choker*, *Nile Royal Bangles*).
- Optical laser tare deduction: distinguishes physical gross weight from net pure gold.
- Bulk Karat re-pricing against live spot fluctuations.

---

## 📁 System Architecture & Directory Layout

```text
3m-dahb/
├── assets/
│   └── images/              # High-resolution generated jewelry product photos
├── css/
│   ├── variables.css        # Complete CSS design tokens (Dark & Light modes)
│   └── style.css            # Responsive layout, tables, cards, and animations
├── js/
│   └── app.js               # Reactive state, cart, scale simulation, and i18n
├── index.html               # Interactive application frontend
├── backend/
│   ├── app/
│   │   ├── core/            # Config, database session, JWT security
│   │   ├── models/          # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/         # Pydantic v2 request/response DTOs
│   │   ├── services/        # Decimal pricing engine & POS tax calculator
│   │   ├── api/v1/          # FastAPI routers (auth, pricing, inventory, pos, dashboard)
│   │   ├── seed.py          # Realistic database seeder
│   │   └── main.py          # FastAPI application factory
│   ├── tests/               # Pytest unit tests for pricing & POS tax
│   ├── requirements.txt
│   └── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Quick Start

### Frontend (Instant Browser Preview)
Simply double-click or open `index.html` in any modern web browser.
- Toggle between **Dark Mode** (AURUM OS) and **Light Mode** (StockPilot PRO) using the `🌓` icon in the top header.
- Switch between **English (LTR)** and **Arabic (RTL)** with the language button.
- Test the **Gold Engine**: change the 24K base rate and click *"Update Global Rate"* to observe real-time price updates across all views.
- Test the **POS Counter**: add pieces to the cart, add a scrap gold trade-in, and click *"Complete Sale & Issue ETA Invoice"*.

### Backend API (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger API Docs: `http://localhost:8000/api/v1/docs`

### Demo Credentials
- **Admin**: `admin@stockpilot.com` / `AdminPass123!` (Full system access & recalibration)
- **Employee**: `cashier@stockpilot.com` / `CashierPass123!` (POS & catalog access)
