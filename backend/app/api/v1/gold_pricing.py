from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from decimal import Decimal
from app.core.database import get_db
from app.core.config import settings
from app.models import GoldPrice, User, AuditLog
from app.schemas import RecalibrateRequest, GoldPricingResponse
from app.services.pricing_engine import PricingEngine, round_money
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/pricing", tags=["Gold Pricing Engine"])

@router.get("/rates", response_model=GoldPricingResponse)
def get_current_rates(db: Session = Depends(get_db)):
    current_prices = db.query(GoldPrice).filter(GoldPrice.is_current == True).all()
    
    # If not seeded or empty, calculate default from settings
    if not current_prices:
        base_rate = settings.DEFAULT_24K_BASE_RATE
        cascade = PricingEngine.calculate_karat_cascade(base_rate)
        for karat, data in cascade.items():
            gp = GoldPrice(
                karat=karat,
                purity_pct=Decimal(str(data["purity_pct"])),
                price_per_gram=Decimal(str(data["price_per_gram"])),
                spread_sell=Decimal(str(data["spread_sell"])),
                source="SAGHA_DESK",
                is_current=True
            )
            db.add(gp)
        db.commit()
        current_prices = db.query(GoldPrice).filter(GoldPrice.is_current == True).all()

    rates_dict = {}
    base_24k = 3420.0
    for p in current_prices:
        if p.karat == "24K":
            base_24k = float(p.price_per_gram)
        rates_dict[p.karat] = {
            "karat": p.karat,
            "purity_pct": float(p.purity_pct),
            "price_per_gram": float(p.price_per_gram),
            "spread_sell": float(p.spread_sell or 0.0),
            "buy_back": float(round_money(p.price_per_gram - Decimal("17.50") if p.karat == "21K" else p.price_per_gram - Decimal("25.00")))
        }

    return GoldPricingResponse(
        base_24k_rate=base_24k,
        lbm_reference_usd=2342.40,
        currency="EGP",
        updated_at=datetime.now(timezone.utc),
        rates=rates_dict
    )

@router.post("/recalibrate", response_model=GoldPricingResponse)
def recalibrate_global_rate(
    payload: RecalibrateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    base_24k = payload.base_24k_rate
    cascade = PricingEngine.calculate_karat_cascade(base_24k)

    # Deactivate current prices
    db.query(GoldPrice).filter(GoldPrice.is_current == True).update({"is_current": False})

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

    # Record audit log
    audit = AuditLog(
        user_id=admin.id,
        action="RECALIBRATE_GOLD_RATES",
        entity="GoldPrice",
        details=f"Master 24K rate updated to {base_24k} EGP/g by {admin.full_name}"
    )
    db.add(audit)
    db.commit()

    return get_current_rates(db)

@router.get("/history")
def get_gold_price_history(db: Session = Depends(get_db)):
    """Returns actual recorded gold spot rate trend points from the database."""
    records = db.query(GoldPrice).filter(
        GoldPrice.karat == "21K"
    ).order_by(GoldPrice.effective_at.desc()).limit(15).all()

    if not records:
        return []

    return [
        {
            "date": p.effective_at.strftime("%b %d") if p.effective_at else "Recent",
            "label": f"{p.effective_at.strftime('%b %d') if p.effective_at else 'Spot'} ({float(p.price_per_gram):,.2f} EGP)",
            "price": float(p.price_per_gram)
        }
        for p in reversed(records)
    ]

@router.get("/live-feed")
async def get_live_market_feed(db: Session = Depends(get_db)):
    """
    Fetches real-time Egyptian gold market prices from primary provider (getdaleelak.com)
    with ETag support and secondary fallback (goldpricestoday.net), saving snapshots to DB.
    """
    from app.services.gold_feed_service import GoldFeedService
    return await GoldFeedService.fetch_market_feed(db=db)

