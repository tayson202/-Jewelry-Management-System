from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import random
from decimal import Decimal
from app.core.database import get_db
from app.core.config import settings
from app.models import Product, Sale, SaleItem, TradeInItem, User, AuditLog
from app.schemas import POSCalculateRequest, POSCheckoutRequest, SaleResponse
from app.services.pos_calculator import POSCalculator
from app.services.pricing_engine import round_money, round_weight
from app.api.deps import get_current_user

router = APIRouter(prefix="/pos", tags=["Point of Sale (POS)"])

def generate_invoice_number():
    year = datetime.now().year
    rand = random.randint(1000, 9999)
    return f"INV-{year}-{rand}"

@router.post("/calculate")
def calculate_cart_preview(payload: POSCalculateRequest):
    items_data = [item.model_dump() for item in payload.items]
    trade_ins_data = [t.model_dump() for t in payload.trade_ins]
    discount = Decimal(str(payload.discount_amount))
    
    result = POSCalculator.calculate_transaction(
        items=items_data,
        scrap_trade_ins=trade_ins_data,
        discount_amount=discount,
        tax_rate_on_making=settings.DEFAULT_TAX_RATE_ON_MAKING
    )
    return result

@router.post("/checkout", response_model=SaleResponse)
def complete_sale(
    payload: POSCheckoutRequest,
    db: Session = Depends(get_db),
    cashier: User = Depends(get_current_user)
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cannot checkout with an empty cart.")

    # 1. Verify availability of every product (prevent selling sold pieces)
    product_ids = [item.product_id for item in payload.items]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    products_by_id = {p.id: p for p in products}

    for item in payload.items:
        p = products_by_id.get(item.product_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found.")
        if p.status == "SOLD":
            raise HTTPException(
                status_code=400,
                detail=f"Item '{p.name}' ({p.sku}) has already been sold! Cannot double-sell."
            )

    # 2. Compute exact financial breakdown
    items_data = [item.model_dump() for item in payload.items]
    trade_ins_data = [t.model_dump() for t in payload.trade_ins]
    discount = Decimal(str(payload.discount_amount))

    calc = POSCalculator.calculate_transaction(
        items=items_data,
        scrap_trade_ins=trade_ins_data,
        discount_amount=discount,
        tax_rate_on_making=settings.DEFAULT_TAX_RATE_ON_MAKING
    )

    # 3. Create Sale record atomically
    invoice_no = generate_invoice_number()
    sale = Sale(
        invoice_number=invoice_no,
        cashier_id=cashier.id,
        customer_id=payload.customer_id,
        total_net_gold_weight=Decimal(str(calc["total_net_gold_weight"])),
        metal_base_value=Decimal(str(calc["metal_base_value"])),
        total_making_charges=Decimal(str(calc["total_making_charges"])),
        gross_goods_subtotal=Decimal(str(calc["gross_goods_subtotal"])),
        scrap_credit_deducted=Decimal(str(calc["scrap_credit_deducted"])),
        statutory_vat=Decimal(str(calc["statutory_vat"])),
        discount_amount=discount,
        net_payable_total=Decimal(str(calc["net_payable_total"])),
        payment_method=payload.payment_method,
        status="COMPLETED"
    )
    db.add(sale)
    db.flush()  # Get sale.id

    # 4. Create Sale Items and mark products as SOLD
    for item_calc in calc["items"]:
        p = products_by_id[item_calc["product_id"]]
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=p.id,
            karat=item_calc["karat"],
            gross_weight=Decimal(str(item_calc["gross_weight"])),
            net_gold_weight=Decimal(str(item_calc["net_gold_weight"])),
            gold_rate_snapshot=Decimal(str(item_calc["gold_rate_snapshot"])),
            making_charge_snapshot=Decimal(str(item_calc["making_charge_snapshot"])),
            item_total=Decimal(str(item_calc["item_total"]))
        )
        db.add(sale_item)

        # Mark unique product as SOLD
        if p.is_unique:
            p.status = "SOLD"
        else:
            p.quantity = max(0, p.quantity - 1)
            if p.quantity == 0:
                p.status = "SOLD"

    # 5. Record Scrap Trade-ins
    for trade_calc in calc["trade_ins"]:
        trade_item = TradeInItem(
            sale_id=sale.id,
            description=trade_calc.get("description", "Customer Scrap Gold Trade-in"),
            karat=trade_calc["karat"],
            gross_weight=Decimal(str(trade_calc["gross_weight"])),
            applied_rate_per_g=Decimal(str(trade_calc["applied_rate_per_g"])),
            total_credit=Decimal(str(trade_calc["total_credit"]))
        )
        db.add(trade_item)

    # 6. Audit log
    audit = AuditLog(
        user_id=cashier.id,
        action="COMPLETE_SALE",
        entity="Sale",
        entity_id=sale.id,
        details=f"Issued invoice {invoice_no} for {calc['net_payable_total']} EGP by cashier {cashier.full_name}"
    )
    db.add(audit)
    db.commit()
    db.refresh(sale)
    return sale

@router.get("/invoices/{invoice_number}")
def get_invoice_details(invoice_number: str, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.invoice_number == invoice_number).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {
        "invoice_number": sale.invoice_number,
        "created_at": sale.created_at,
        "cashier": sale.cashier.full_name if sale.cashier else "Staff",
        "customer": sale.customer.full_name if sale.customer else "Walk-in Guest",
        "customer_phone": sale.customer.phone if sale.customer else None,
        "customer_tier": sale.customer.vip_tier if sale.customer else "Standard",
        "total_net_gold_weight": float(sale.total_net_gold_weight),
        "metal_base_value": float(sale.metal_base_value),
        "total_making_charges": float(sale.total_making_charges),
        "gross_goods_subtotal": float(sale.gross_goods_subtotal),
        "scrap_credit_deducted": float(sale.scrap_credit_deducted),
        "statutory_vat": float(sale.statutory_vat),
        "discount_amount": float(sale.discount_amount),
        "net_payable_total": float(sale.net_payable_total),
        "payment_method": sale.payment_method,
        "status": sale.status,
        "items": [
            {
                "product_name": item.product.name if item.product else "Jewelry Item",
                "product_name_ar": item.product.name_ar if item.product else "قطعة مجوهرات",
                "sku": item.product.sku if item.product else "N/A",
                "karat": item.karat,
                "gross_weight": float(item.gross_weight),
                "net_gold_weight": float(item.net_gold_weight),
                "gold_rate_snapshot": float(item.gold_rate_snapshot),
                "making_charge_snapshot": float(item.making_charge_snapshot),
                "item_total": float(item.item_total)
            }
            for item in sale.items
        ],
        "trade_ins": [
            {
                "description": t.description,
                "karat": t.karat,
                "gross_weight": float(t.gross_weight),
                "applied_rate_per_g": float(t.applied_rate_per_g),
                "total_credit": float(t.total_credit)
            }
            for t in sale.trade_ins
        ]
    }
