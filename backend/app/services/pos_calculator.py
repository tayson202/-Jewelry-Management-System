from decimal import Decimal
from typing import List, Dict, Any
from app.services.pricing_engine import round_money, round_weight

class POSCalculator:
    @staticmethod
    def calculate_transaction(
        items: List[Dict[str, Any]],
        scrap_trade_ins: List[Dict[str, Any]] = None,
        discount_amount: Decimal = Decimal("0.00"),
        tax_rate_on_making: Decimal = Decimal("0.14")
    ) -> Dict[str, Any]:
        """
        Calculates exact jewelry invoice totals:
        - Pure gold metal value based on net weight
        - Workmanship / Making fee
        - Scrap trade-in deduction
        - Egyptian Tax Authority (ETA) 14% VAT on Making Charges Only
        - Net payable total
        """
        scrap_trade_ins = scrap_trade_ins or []
        
        total_net_gold_weight = Decimal("0.000")
        total_gross_weight = Decimal("0.000")
        total_metal_base_value = Decimal("0.00")
        total_making_charges = Decimal("0.00")
        
        calculated_items = []
        for item in items:
            net_gold_wt = Decimal(str(item.get("net_gold_weight", item.get("gross_weight", 0))))
            gross_wt = Decimal(str(item.get("gross_weight", 0)))
            rate_per_g = Decimal(str(item.get("gold_rate_snapshot", 0)))
            making_rate = Decimal(str(item.get("making_charge_snapshot", 0)))
            charge_type = item.get("making_charge_type", "PER_GRAM")

            metal_value = round_money(net_gold_wt * rate_per_g)
            if charge_type == "FLAT":
                making_val = round_money(making_rate)
            else:
                making_val = round_money(gross_wt * making_rate)

            item_total = metal_value + making_val
            
            total_net_gold_weight += net_gold_wt
            total_gross_weight += gross_wt
            total_metal_base_value += metal_value
            total_making_charges += making_val

            calculated_items.append({
                **item,
                "metal_value": float(metal_value),
                "making_charges": float(making_val),
                "item_total": float(item_total)
            })

        gross_goods_subtotal = total_metal_base_value + total_making_charges

        # Calculate Customer Scrap Trade-in Credit
        total_scrap_credit = Decimal("0.00")
        calculated_trade_ins = []
        for trade in scrap_trade_ins:
            wt = Decimal(str(trade.get("gross_weight", 0)))
            rate = Decimal(str(trade.get("applied_rate_per_g", 0)))
            credit = round_money(wt * rate)
            total_scrap_credit += credit
            calculated_trade_ins.append({
                **trade,
                "total_credit": float(credit)
            })

        # ETA Sales Tax: 14% on Making Charges Only (standard Egyptian gold law)
        statutory_tax = round_money(total_making_charges * tax_rate_on_making)

        # Net Payable
        net_payable = (gross_goods_subtotal - total_scrap_credit + statutory_tax - discount_amount)
        if net_payable < Decimal("0.00"):
            net_payable = Decimal("0.00")

        return {
            "items": calculated_items,
            "trade_ins": calculated_trade_ins,
            "total_net_gold_weight": float(round_weight(total_net_gold_weight)),
            "total_gross_weight": float(round_weight(total_gross_weight)),
            "metal_base_value": float(total_metal_base_value),
            "total_making_charges": float(total_making_charges),
            "gross_goods_subtotal": float(gross_goods_subtotal),
            "scrap_credit_deducted": float(total_scrap_credit),
            "statutory_vat": float(statutory_tax),
            "discount_amount": float(discount_amount),
            "net_payable_total": float(net_payable)
        }
