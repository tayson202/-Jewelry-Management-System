from decimal import Decimal
import pytest
from app.services.pos_calculator import POSCalculator

def test_pos_transaction_with_scrap_and_tax():
    # Matching the exact Figma POS calculation:
    items = [
        {
            "product_id": "item-1",
            "karat": "21K",
            "gross_weight": 6.80,
            "net_gold_weight": 6.80,
            "gold_rate_snapshot": 2992.50,
            "making_charge_snapshot": 180.00,
            "making_charge_type": "PER_GRAM"
        },
        {
            "product_id": "item-2",
            "karat": "18K",
            "gross_weight": 5.20,
            "net_gold_weight": 4.60,
            "gold_rate_snapshot": 2565.00,
            "making_charge_snapshot": 320.00,
            "making_charge_type": "PER_GRAM"
        }
    ]

    trade_ins = [
        {
            "description": "Old 18K Scrap Ring",
            "karat": "18K",
            "gross_weight": 12.40,
            "applied_rate_per_g": 2565.00
        }
    ]

    result = POSCalculator.calculate_transaction(
        items=items,
        scrap_trade_ins=trade_ins,
        discount_amount=Decimal("0.00"),
        tax_rate_on_making=Decimal("0.14")
    )

    # 1. Total Net Gold Weight: 6.80 + 4.60 = 11.40 g
    assert result["total_net_gold_weight"] == 11.400

    # 2. Making Charges: (6.80 * 180) + (5.20 * 320) = 1224 + 1664 = 2888.00
    assert result["total_making_charges"] == 2888.00

    # 3. Scrap Credit: 12.40 * 2565.00 = 31806.00
    assert result["scrap_credit_deducted"] == 31806.00

    # 4. ETA Sales Tax (14% on Making Only): 2888 * 0.14 = 404.32
    assert result["statutory_vat"] == 404.32

    # 5. Net Payable Total must be positive and non-negative
    assert result["net_payable_total"] >= 0.0
