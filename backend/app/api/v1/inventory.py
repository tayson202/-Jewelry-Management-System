from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from app.core.database import get_db
from app.models import Product, GoldPrice, User, AuditLog
from app.schemas import ProductCreate, ProductResponse
from app.services.pricing_engine import KARAT_PURITY_RATIOS, round_money, round_weight
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/inventory", tags=["Inventory Vault"])

@router.get("", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = None,
    karat: Optional[str] = None,
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    min_weight: Optional[float] = None,
    max_weight: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if search:
        s = f"%{search}%"
        query = query.filter((Product.name.ilike(s)) | (Product.sku.ilike(s)) | (Product.name_ar.ilike(s)))
    if karat and karat != "ALL":
        query = query.filter(Product.karat == karat)
    if status and status != "ALL":
        query = query.filter(Product.status == status)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_weight is not None:
        query = query.filter(Product.gross_weight >= min_weight)
    if max_weight is not None:
        query = query.filter(Product.gross_weight <= max_weight)
    
    return query.order_by(Product.created_at.desc()).all()

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    item_in: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Verify unique SKU
    existing = db.query(Product).filter(Product.sku == item_in.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product with SKU '{item_in.sku}' already exists.")

    gross = item_in.gross_weight
    tare = item_in.stone_tare
    if tare > gross:
        raise HTTPException(status_code=400, detail="Stone tare weight cannot exceed gross weight.")
    
    net_gold = round_weight(gross - tare)
    ratio = KARAT_PURITY_RATIOS.get(item_in.karat, Decimal("0.875"))
    purity_pct = round_money(ratio * Decimal("100"))

    # Fetch current spot price for this karat to calculate initial retail
    gold_price = db.query(GoldPrice).filter(GoldPrice.karat == item_in.karat, GoldPrice.is_current == True).first()
    rate = gold_price.price_per_gram if gold_price else Decimal("3000.00")

    metal_val = round_money(net_gold * rate)
    if item_in.making_charge_type == "FLAT":
        making_val = round_money(item_in.making_charge_rate)
    else:
        making_val = round_money(gross * item_in.making_charge_rate)
    retail_price = metal_val + making_val

    product = Product(
        sku=item_in.sku,
        barcode=item_in.barcode or item_in.sku,
        name=item_in.name,
        name_ar=item_in.name_ar,
        category_id=item_in.category_id,
        karat=item_in.karat,
        purity_pct=purity_pct,
        gross_weight=gross,
        stone_tare=tare,
        net_gold_weight=net_gold,
        making_charge_type=item_in.making_charge_type,
        making_charge_rate=item_in.making_charge_rate,
        retail_price=retail_price,
        is_unique=item_in.is_unique,
        quantity=item_in.quantity,
        image_url=item_in.image_url,
        hallmark_code=item_in.hallmark_code or "18K • 750 HALLMARK",
        status="IN_STOCK"
    )
    db.add(product)
    
    audit = AuditLog(
        user_id=user.id,
        action="CREATE_PRODUCT",
        entity="Product",
        entity_id=product.id,
        details=f"Added {item_in.name} ({item_in.sku}), Net: {net_gold}g, Retail: {retail_price} EGP"
    )
    db.add(audit)
    db.commit()
    db.refresh(product)
    return product

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/bulk-reprice")
def bulk_reprice_inventory(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Recalculates retail values of all IN_STOCK items using current gold spot prices."""
    current_prices = {
        gp.karat: gp.price_per_gram 
        for gp in db.query(GoldPrice).filter(GoldPrice.is_current == True).all()
    }
    
    in_stock = db.query(Product).filter(Product.status == "IN_STOCK").all()
    updated_count = 0
    for p in in_stock:
        rate = current_prices.get(p.karat)
        if rate:
            metal_val = round_money(p.net_gold_weight * rate)
            if p.making_charge_type == "FLAT":
                making_val = p.making_charge_rate
            else:
                making_val = round_money(p.gross_weight * p.making_charge_rate)
            p.retail_price = metal_val + making_val
            updated_count += 1

    audit = AuditLog(
        user_id=admin.id,
        action="BULK_REPRICE",
        entity="Inventory",
        details=f"Recalculated valuation for {updated_count} items against live spot."
    )
    db.add(audit)
    db.commit()
    return {"message": f"Successfully re-priced {updated_count} jewelry pieces.", "count": updated_count}
