from decimal import Decimal
from datetime import datetime, timezone
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import User, GoldPrice, Category, Product, Customer, Supplier, Sale, SaleItem, TradeInItem, AuditLog
from app.services.pricing_engine import PricingEngine

def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("🌱 Seeding StockPilot / AURUM OS database...")

    # Clear existing tables
    db.query(TradeInItem).delete()
    db.query(SaleItem).delete()
    db.query(Sale).delete()
    db.query(Product).delete()
    db.query(Category).delete()
    db.query(Customer).delete()
    db.query(Supplier).delete()
    db.query(GoldPrice).delete()
    db.query(AuditLog).delete()
    db.query(User).delete()
    db.commit()

    # 1. Users
    admin_user = User(
        email="admin@stockpilot.com",
        full_name="Mona Al-Sayed (Shop Admin)",
        hashed_password=get_password_hash("AdminPass123!"),
        role="ADMIN"
    )
    cashier_user = User(
        email="cashier@stockpilot.com",
        full_name="Tariq Al-Fahim (Senior Appraiser)",
        hashed_password=get_password_hash("CashierPass123!"),
        role="EMPLOYEE"
    )
    db.add_all([admin_user, cashier_user])
    db.flush()

    # 2. Gold Prices (Master 24K: 3,420 EGP/g)
    base_rate = Decimal("3420.00")
    cascade = PricingEngine.calculate_karat_cascade(base_rate)
    for karat, data in cascade.items():
        gp = GoldPrice(
            karat=karat,
            purity_pct=Decimal(str(data["purity_pct"])),
            price_per_gram=Decimal(str(data["price_per_gram"])),
            spread_sell=Decimal(str(data["spread_sell"])),
            source="SAGHA_DESK",
            is_current=True,
            effective_at=datetime.now(timezone.utc)
        )
        db.add(gp)
    db.flush()

    # 3. Categories
    cat_rings = Category(name="Rings", name_ar="خواتم", slug="rings", default_making_charge=Decimal("180.00"), floor_margin_pct=Decimal("12.00"))
    cat_necklaces = Category(name="Necklaces & Chains", name_ar="عقود وسلاسل", slug="necklaces", default_making_charge=Decimal("195.00"), floor_margin_pct=Decimal("12.00"))
    cat_bangles = Category(name="Bracelets & Bangles", name_ar="أساور وبناجر", slug="bangles", default_making_charge=Decimal("190.00"), floor_margin_pct=Decimal("15.00"))
    cat_bullion = Category(name="Bullion & Coins", name_ar="سبائك وعملات", slug="bullion", default_making_charge=Decimal("45.00"), floor_margin_pct=Decimal("5.00"))
    cat_earrings = Category(name="Earrings", name_ar="أقراط وحلقان", slug="earrings", default_making_charge=Decimal("250.00"), floor_margin_pct=Decimal("18.00"))
    db.add_all([cat_rings, cat_necklaces, cat_bangles, cat_bullion, cat_earrings])
    db.flush()

    # 4. Customers
    cust1 = Customer(
        full_name="Laila Nour El-Din",
        phone="+20 100 892 4110",
        vip_tier="VIP Tier 1",
        loyalty_points=4200,
        notes="High-value client. Prefers 21K traditional Egyptian designs and bridal suites."
    )
    cust2 = Customer(
        full_name="Dr. Farida Mansour",
        phone="+20 108 892 4411",
        vip_tier="Gold Tier",
        loyalty_points=2400,
        notes="Collects Italian 18K diamond pieces."
    )
    db.add_all([cust1, cust2])
    db.flush()

    # 5. Suppliers
    sup1 = Supplier(
        name="Central Egyptian Bullion Clearinghouse (Sagha Desk)",
        company_name="Sagha Bullion Trading Co.",
        phone="+20 2 2590 1200",
        balance_egp=Decimal("1248650.00")
    )
    sup2 = Supplier(
        name="Vicenza Luxury Mounts Italy",
        company_name="Vicenza Oro SpA",
        phone="+39 0444 123456",
        balance_egp=Decimal("450000.00")
    )
    db.add_all([sup1, sup2])
    db.flush()

    # 6. Realistic Inventory Pieces matching Figma screenshots
    products = [
        Product(
            sku="AUR-7841-SOL",
            barcode="890124801",
            name="Aethelred Solitaire Royale",
            name_ar="خاتم سوليتير أثيلريد الملكي 18 قيراط",
            category_id=cat_rings.id,
            karat="18K",
            purity_pct=Decimal("75.00"),
            gross_weight=Decimal("14.820"),
            stone_tare=Decimal("2.720"),
            net_gold_weight=Decimal("12.100"),
            making_charge_type="PER_GRAM",
            making_charge_rate=Decimal("450.00"),
            retail_price=Decimal("73850.00"),
            status="IN_STOCK",
            is_unique=True,
            image_url="assets/images/diamond_solitaire_ring_1792597878725.jpg",
            hallmark_code="18K • 750 HALLMARK (EPC-E280-0019)"
        ),
        Product(
            sku="AUR-9904",
            barcode="771890215",
            name="Vendôme Floral Choker",
            name_ar="طوق فاندوم الزهري عيار 21",
            category_id=cat_necklaces.id,
            karat="21K",
            purity_pct=Decimal("87.50"),
            gross_weight=Decimal("38.400"),
            stone_tare=Decimal("0.000"),
            net_gold_weight=Decimal("38.400"),
            making_charge_type="PER_GRAM",
            making_charge_rate=Decimal("280.00"),
            retail_price=Decimal("125650.00"),
            status="IN_STOCK",
            is_unique=True,
            image_url="assets/images/byzantine_gold_choker_1792598803717.jpg",
            hallmark_code="21K • 875 EGYPTIAN STANDARD"
        ),
        Product(
            sku="AUR-7731",
            barcode="622100984",
            name="Nile Royal Bangle Pair",
            name_ar="زوج أساور النيل الملكية عيار 21",
            category_id=cat_bangles.id,
            karat="21K",
            purity_pct=Decimal("87.50"),
            gross_weight=Decimal("54.200"),
            stone_tare=Decimal("0.000"),
            net_gold_weight=Decimal("54.200"),
            making_charge_type="PER_GRAM",
            making_charge_rate=Decimal("190.00"),
            retail_price=Decimal("172500.00"),
            status="IN_STOCK",
            is_unique=True,
            image_url="assets/images/cleopatra_gold_cuff_1792598857432.jpg",
            hallmark_code="21K • 875 CAIRO HALLMARK"
        ),
        Product(
            sku="AUR-2401",
            barcode="764015891",
            name="PAMP Suisse Fine Ingot 50g",
            name_ar="سبيكة بامب سويسرا 50 جرام عيار 24",
            category_id=cat_bullion.id,
            karat="24K",
            purity_pct=Decimal("99.99"),
            gross_weight=Decimal("50.000"),
            stone_tare=Decimal("0.000"),
            net_gold_weight=Decimal("50.000"),
            making_charge_type="FLAT",
            making_charge_rate=Decimal("65.00"),
            retail_price=Decimal("174250.00"),
            status="IN_STOCK",
            is_unique=False,
            quantity=5,
            image_url="assets/images/gold_bullion_sovereign_1792598760193.jpg",
            hallmark_code="999.9 ESSAYEUR FONDEUR"
        ),
        Product(
            sku="21K-RN-092",
            barcode="21092001",
            name="Royal Damascene Ring",
            name_ar="خاتم دمشقي أثري منقوش عيار 21",
            category_id=cat_rings.id,
            karat="21K",
            purity_pct=Decimal("87.50"),
            gross_weight=Decimal("6.800"),
            stone_tare=Decimal("0.000"),
            net_gold_weight=Decimal("6.800"),
            making_charge_type="PER_GRAM",
            making_charge_rate=Decimal("180.00"),
            retail_price=Decimal("21569.00"),
            status="IN_STOCK",
            is_unique=True,
            image_url="assets/images/damascene_gold_ring_1792598690682.jpg",
            hallmark_code="21K • 875 KHAN EL-KHALILI"
        ),
        Product(
            sku="18K-SL-418",
            barcode="18418002",
            name="Etoile Pavé Solitaire",
            name_ar="خاتم إتوال بافيه سوليتير 18 قيراط مع ألماس",
            category_id=cat_rings.id,
            karat="18K",
            purity_pct=Decimal("75.00"),
            gross_weight=Decimal("5.200"),
            stone_tare=Decimal("0.600"),
            net_gold_weight=Decimal("4.600"),
            making_charge_type="PER_GRAM",
            making_charge_rate=Decimal("320.00"),
            retail_price=Decimal("27800.00"),
            status="IN_STOCK",
            is_unique=True,
            image_url="assets/images/diamond_solitaire_ring_1792597878725.jpg",
            hallmark_code="18K • 750 DIA 0.85ct"
        ),
        Product(
            sku="24K-COIN-08",
            barcode="24008003",
            name="George Sovereign Bullion",
            name_ar="جنيه جورج ذهب إنجليزي عيار 24",
            category_id=cat_bullion.id,
            karat="24K",
            purity_pct=Decimal("99.99"),
            gross_weight=Decimal("8.000"),
            stone_tare=Decimal("0.000"),
            net_gold_weight=Decimal("8.000"),
            making_charge_type="PER_GRAM",
            making_charge_rate=Decimal("45.00"),
            retail_price=Decimal("27880.00"),
            status="IN_STOCK",
            is_unique=False,
            quantity=12,
            image_url="assets/images/gold_bullion_sovereign_1792598760193.jpg",
            hallmark_code="ROYAL MINT SOVEREIGN 999.9"
        ),
        Product(
            sku="21K-CH-551",
            barcode="21551004",
            name="Byzantine Link Choker",
            name_ar="طوق بيزنطي يدوي عيار 21",
            category_id=cat_necklaces.id,
            karat="21K",
            purity_pct=Decimal("87.50"),
            gross_weight=Decimal("13.200"),
            stone_tare=Decimal("0.000"),
            net_gold_weight=Decimal("13.200"),
            making_charge_type="PER_GRAM",
            making_charge_rate=Decimal("195.00"),
            retail_price=Decimal("42075.00"),
            status="IN_STOCK",
            is_unique=True,
            image_url="assets/images/byzantine_gold_choker_1792598803717.jpg",
            hallmark_code="21K • 875 HANDCRAFTED"
        ),
        Product(
            sku="21K-BG-803",
            barcode="21803006",
            name="Cleopatra Cuffed Bangle",
            name_ar="إسورة كليوباترا العريضة عيار 21 بنقوش فرعونية",
            category_id=cat_bangles.id,
            karat="21K",
            purity_pct=Decimal("87.50"),
            gross_weight=Decimal("18.500"),
            stone_tare=Decimal("0.000"),
            net_gold_weight=Decimal("18.500"),
            making_charge_type="PER_GRAM",
            making_charge_rate=Decimal("210.00"),
            retail_price=Decimal("59246.00"),
            status="IN_STOCK",
            is_unique=True,
            image_url="assets/images/cleopatra_gold_cuff_1792598857432.jpg",
            hallmark_code="21K • 875 SOLID SPRING LOCK"
        )
    ]
    db.add_all(products)
    db.commit()

    print(f"✅ Seeding complete! Added {len(products)} authentic jewelry items, gold prices, categories, and users.")
    db.close()

if __name__ == "__main__":
    run_seed()
