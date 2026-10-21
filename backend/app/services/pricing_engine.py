from decimal import Decimal, ROUND_HALF_UP

KARAT_PURITY_RATIOS = {
    "24K": Decimal("24") / Decimal("24"),   # 1.0000 (100%)
    "22K": Decimal("22") / Decimal("24"),   # 0.9167 (91.67%)
    "21K": Decimal("21") / Decimal("24"),   # 0.8750 (87.50%)
    "18K": Decimal("18") / Decimal("24"),   # 0.7500 (75.00%)
    "14K": Decimal("14") / Decimal("24"),   # 0.5833 (58.33%)
}

def round_money(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def round_weight(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

class PricingEngine:
    @staticmethod
    def calculate_karat_cascade(base_24k_rate: Decimal) -> dict:
        """
        Takes the Master 24K pure bullion rate (EGP/g) and calculates
        the official Egyptian Sagha and institutional rates for 22K, 21K, 18K, 14K.
        """
        rates = {}
        for karat, ratio in KARAT_PURITY_RATIOS.items():
            raw_rate = base_24k_rate * ratio
            purity_pct = (ratio * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
            # Sagha spreads (as seen in Figma screen):
            spread_sell = Decimal("45.00") if karat == "22K" else (
                Decimal("0.00") if karat == "21K" else (
                    Decimal("60.00") if karat == "18K" else (
                        Decimal("35.00") if karat == "14K" else Decimal("0.00")
                    )
                )
            )
            buy_back = (round_money(raw_rate) - Decimal("17.50")) if karat == "21K" else (round_money(raw_rate) - Decimal("25.00"))

            rates[karat] = {
                "karat": karat,
                "purity_pct": float(purity_pct),
                "price_per_gram": float(round_money(raw_rate)),
                "spread_sell": float(spread_sell),
                "buy_back": float(round_money(buy_back))
            }
        return rates

    @staticmethod
    def calculate_metal_value(net_gold_weight: Decimal, karat_price_per_gram: Decimal) -> Decimal:
        return round_money(net_gold_weight * karat_price_per_gram)

    @staticmethod
    def calculate_making_charge(gross_weight: Decimal, rate_per_gram: Decimal, charge_type: str = "PER_GRAM") -> Decimal:
        if charge_type == "FLAT":
            return round_money(rate_per_gram)
        return round_money(gross_weight * rate_per_gram)
