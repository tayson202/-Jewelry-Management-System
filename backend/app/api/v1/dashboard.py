from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timezone
from decimal import Decimal
from app.core.database import get_db
from app.models import Product, Sale, GoldPrice
from app.schemas import DashboardMetricsResponse
from app.services.pricing_engine import KARAT_PURITY_RATIOS

router = APIRouter(prefix="/dashboard", tags=["Executive Dashboard"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    # 1. Total vault valuation of in-stock items
    in_stock_products = db.query(Product).filter(
        Product.status == "IN_STOCK",
        Product.is_archived == False
    ).all()
    total_val = sum((p.retail_price for p in in_stock_products), Decimal("0.00"))
    
    # 2. Total pure 24K gold weight
    pure_weight = Decimal("0.000")
    for p in in_stock_products:
        ratio = KARAT_PURITY_RATIOS.get(p.karat, Decimal("0.875"))
        pure_weight += p.net_gold_weight * ratio

    # 3. Today's POS Sales
    today = date.today()
    todays_sales = db.query(Sale).filter(
        func.date(Sale.created_at) == today,
        Sale.status == "COMPLETED"
    ).all()
    
    todays_total = sum((s.net_payable_total for s in todays_sales), Decimal("0.00"))
    todays_orders = len(todays_sales)
    
    # 4. Realized margin today (making charges)
    realized_margin = sum((s.total_making_charges for s in todays_sales), Decimal("0.00"))

    # 5. Real workshop/custom pieces in progress
    workshop_pieces = db.query(Product).filter(
        Product.status == "WORKSHOP",
        Product.is_archived == False
    ).count()

    # 6. Real low stock alerts
    low_stock_count = db.query(Product).filter(
        Product.is_archived == False,
        Product.quantity <= Product.min_stock_alert,
        Product.status == "IN_STOCK"
    ).count()

    return DashboardMetricsResponse(
        vault_total_valuation=float(total_val),
        total_vault_pure_weight=float(pure_weight),
        todays_pos_sales=float(todays_total),
        todays_orders_count=todays_orders,
        realized_margin=float(realized_margin),
        active_atelier_pieces=workshop_pieces,
        low_stock_count=low_stock_count
    )

@router.get("/karat-mix")
def get_karat_mix(db: Session = Depends(get_db)):
    """Computes real assayed weight distribution by Karat from active inventory."""
    in_stock = db.query(Product).filter(
        Product.status == "IN_STOCK",
        Product.is_archived == False
    ).all()
    if not in_stock:
        return []

    karat_weights = {}
    total_w = Decimal("0.000")
    for p in in_stock:
        k = p.karat
        w = Decimal(str(p.gross_weight))
        karat_weights[k] = karat_weights.get(k, Decimal("0.000")) + w
        total_w += w

    karat_names = {
        "21K": "21K Egyptian Standard",
        "18K": "18K Italian Mounts & Sets",
        "24K": "24K Minted Bars & Bullion",
        "22K": "22K Traditional Gulf Filigree",
        "14K": "14K Commercial Jewelry",
        "12K": "12K Lightweight Gold"
    }

    mix = []
    for k, w in sorted(karat_weights.items(), key=lambda x: x[1], reverse=True):
        pct = round(float(w / total_w * Decimal("100")), 1) if total_w > 0 else 0.0
        mix.append({
            "karat": k,
            "name": karat_names.get(k, f"{k} Gold"),
            "weight_g": float(w),
            "percentage": pct
        })
    return mix

@router.get("/trend")
def get_sales_vs_gold_trend(db: Session = Depends(get_db)):
    """Returns actual completed sales volume over recent days or empty array if fresh shop."""
    sales = db.query(
        func.date(Sale.created_at).label("sale_date"),
        func.sum(Sale.net_payable_total).label("total_volume"),
        func.count(Sale.id).label("slips_count")
    ).filter(
        Sale.status == "COMPLETED"
    ).group_by(
        func.date(Sale.created_at)
    ).order_by(
        func.date(Sale.created_at).desc()
    ).limit(7).all()

    if not sales:
        return []

    # Get latest gold spot rate for reference
    current_gold = db.query(GoldPrice).filter(GoldPrice.karat == "21K", GoldPrice.is_current == True).first()
    spot_rate = float(current_gold.price_per_gram) if current_gold else 0.0

    return [
        {
            "period": str(row.sale_date),
            "sales_volume": float(row.total_volume or 0.0),
            "gold_spot": spot_rate,
            "orders": row.slips_count
        }
        for row in reversed(sales)
    ]

