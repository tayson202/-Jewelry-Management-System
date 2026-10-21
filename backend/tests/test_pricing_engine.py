from decimal import Decimal
import pytest
from app.services.pricing_engine import PricingEngine, KARAT_PURITY_RATIOS, round_money

def test_karat_cascade_calculations():
    base_24k = Decimal("3420.00")
    cascade = PricingEngine.calculate_karat_cascade(base_24k)

    # 24K should be 3420.00
    assert cascade["24K"]["price_per_gram"] == 3420.00
    assert cascade["24K"]["purity_pct"] == 100.00

    # 21K should be 3420 * (21/24) = 2992.50
    assert cascade["21K"]["price_per_gram"] == 2992.50
    assert cascade["21K"]["purity_pct"] == 87.50

    # 18K should be 3420 * (18/24) = 2565.00
    assert cascade["18K"]["price_per_gram"] == 2565.00
    assert cascade["18K"]["purity_pct"] == 75.00

def test_metal_value_and_making_charges():
    net_gold = Decimal("12.100")
    rate_18k = Decimal("2565.00")
    metal_val = PricingEngine.calculate_metal_value(net_gold, rate_18k)
    # 12.100 * 2565 = 31036.50
    assert metal_val == Decimal("31036.50")

    gross_wt = Decimal("14.820")
    making_fee = Decimal("450.00")
    making_total = PricingEngine.calculate_making_charge(gross_wt, making_fee, charge_type="PER_GRAM")
    # 14.820 * 450 = 6669.00
    assert making_total == Decimal("6669.00")
