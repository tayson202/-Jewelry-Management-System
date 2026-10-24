import httpx
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, List
import logging
from sqlalchemy.orm import Session
from app.models import GoldPrice

logger = logging.getLogger(__name__)

PRIMARY_FEED_URL = "https://getdaleelak.com/api/v1/feed.json"
SECONDARY_FEED_URL = "https://goldpricestoday.net/api/v1/egypt.json"

# In-memory feed cache for ETag handling and offline resilience
_FEED_CACHE: Dict[str, Any] = {
    "etag": None,
    "last_modified": None,
    "last_valid_data": None,
    "last_retrieved_at": None,
    "previous_snapshot": None,
}

KARAT_PURITIES = {
    "24K": {"purity_pct": 99.9, "factor": Decimal("24") / Decimal("24")},
    "22K": {"purity_pct": 91.6, "factor": Decimal("22") / Decimal("24")},
    "21K": {"purity_pct": 87.5, "factor": Decimal("21") / Decimal("24")},
    "18K": {"purity_pct": 75.0, "factor": Decimal("18") / Decimal("24")},
    "14K": {"purity_pct": 58.3, "factor": Decimal("14") / Decimal("24")},
    "12K": {"purity_pct": 50.0, "factor": Decimal("12") / Decimal("24")},
}

class GoldFeedService:
    @classmethod
    async def fetch_market_feed(cls, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Fetches live Egyptian gold market prices with ETag caching,
        provider fallback, movement tracking, and optional DB persistence.
        """
        now_utc = datetime.now(timezone.utc)
        headers = {
            "Accept": "application/json",
            "User-Agent": "3M-Dahab-OS/1.0 (Egyptian Gold Market Monitor)"
        }
        if _FEED_CACHE["etag"]:
            headers["If-None-Match"] = _FEED_CACHE["etag"]

        # 1. Attempt Primary Provider: Daleelak
        primary_response = None
        is_304 = False
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(PRIMARY_FEED_URL, headers=headers)
                if resp.status_code == 304 and _FEED_CACHE["last_valid_data"]:
                    is_304 = True
                    _FEED_CACHE["last_retrieved_at"] = now_utc.isoformat()
                    return _FEED_CACHE["last_valid_data"]
                elif resp.status_code == 200:
                    primary_response = resp
                    _FEED_CACHE["etag"] = resp.headers.get("ETag")
                    _FEED_CACHE["last_modified"] = resp.headers.get("Last-Modified")
        except Exception as e:
            logger.warning(f"Daleelak primary feed request failed: {e}")

        # 2. Parse primary response if successful
        if primary_response:
            try:
                feed_json = primary_response.json()
                mapped_data = cls._parse_daleelak_feed(feed_json, now_utc)
                cls._update_movement_and_cache(mapped_data, now_utc)
                if db:
                    cls._persist_snapshots_to_db(db, mapped_data)
                return mapped_data
            except Exception as e:
                logger.error(f"Failed to parse Daleelak feed response: {e}")

        # 3. Fallback to Secondary Provider: GoldPricesToday
        logger.info("Attempting fallback to secondary provider: goldpricestoday.net")
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                sec_resp = await client.get(SECONDARY_FEED_URL, headers={"Accept": "application/json"})
                if sec_resp.status_code == 200:
                    sec_json = sec_resp.json()
                    mapped_data = cls._parse_goldpricestoday_feed(sec_json, now_utc)
                    cls._update_movement_and_cache(mapped_data, now_utc)
                    if db:
                        cls._persist_snapshots_to_db(db, mapped_data)
                    return mapped_data
        except Exception as e:
            logger.warning(f"Secondary feed request failed: {e}")

        # 4. If both failed, return cached snapshot in Offline mode
        if _FEED_CACHE["last_valid_data"]:
            offline_data = dict(_FEED_CACHE["last_valid_data"])
            offline_data["status"] = "offline"
            offline_data["warning"] = "Operating in offline mode. Displaying last verified market snapshot."
            offline_data["retrieved_at"] = now_utc.isoformat()
            return offline_data

        # 5. Last resort fallback
        return cls._create_offline_mock_data(now_utc)

    @classmethod
    def _parse_daleelak_feed(cls, feed: Dict[str, Any], now_utc: datetime) -> Dict[str, Any]:
        assets = {a.get("id"): a for a in feed.get("assets", []) if isinstance(a, dict)}
        generated_at = feed.get("generatedAt", now_utc.isoformat())

        g24 = assets.get("GOLD24K-EGP", {})
        g21 = assets.get("GOLD21K-EGP", {})
        g18 = assets.get("GOLD18K-EGP", {})
        gpound = assets.get("GOLDPOUND-EGP", {})
        usd_asset = assets.get("USD-EGP", {})

        observed_at = g24.get("observedAt") or g21.get("observedAt") or generated_at
        freshness_info = g24.get("freshness", {})
        is_fresh = freshness_info.get("state") == "fresh" and not freshness_info.get("stale", False)

        # Extract verified buy/sell rates for 24K, 21K, 18K
        karats: Dict[str, Any] = {}

        for karat_name, asset in [("24K", g24), ("21K", g21), ("18K", g18)]:
            if asset:
                best_buy = asset.get("directions", {}).get("buy", {}).get("best", {})
                best_sell = asset.get("directions", {}).get("sell", {}).get("best", {})
                sell_val = float(best_sell.get("value") or 0.0)
                buy_val = float(best_buy.get("value") or 0.0)

                # Provider perspective:
                # Sell = Shop/Provider charges to customer
                # Buy = Shop/Provider pays customer
                seller_name = best_sell.get("seller") or best_buy.get("seller") or "Sagha Market"

                karats[karat_name] = {
                    "karat": karat_name,
                    "purity_pct": KARAT_PURITIES[karat_name]["purity_pct"],
                    "sell_price": sell_val,
                    "buy_price": buy_val,
                    "spread": round(sell_val - buy_val, 2) if sell_val and buy_val else 0.0,
                    "source": "getdaleelak.com",
                    "best_seller": seller_name,
                    "observed_at": asset.get("observedAt", observed_at),
                    "is_indicative": False,
                    "movement": {"change_egp": 0.0, "change_pct": 0.0, "direction": "flat"}
                }

        # Derive 22K, 14K, 12K from 24K rate with explicit indicative label
        base_24k_sell = karats.get("24K", {}).get("sell_price", 0.0)
        base_24k_buy = karats.get("24K", {}).get("buy_price", 0.0)

        for karat_name in ["22K", "14K", "12K"]:
            factor = float(KARAT_PURITIES[karat_name]["factor"])
            est_sell = round(base_24k_sell * factor, 2)
            est_buy = round(base_24k_buy * factor, 2)
            karats[karat_name] = {
                "karat": karat_name,
                "purity_pct": KARAT_PURITIES[karat_name]["purity_pct"],
                "sell_price": est_sell,
                "buy_price": est_buy,
                "spread": round(est_sell - est_buy, 2),
                "source": "Indicative Benchmark (عيار استرشادي)",
                "best_seller": "Derived from 24K Sagha Standard",
                "observed_at": observed_at,
                "is_indicative": True,
                "movement": {"change_egp": 0.0, "change_pct": 0.0, "direction": "flat"}
            }

        # Gold Pound (8 grams of 21K)
        pound_sell = gpound.get("directions", {}).get("sell", {}).get("best", {}).get("value")
        pound_buy = gpound.get("directions", {}).get("buy", {}).get("best", {}).get("value")
        if not pound_sell and karats.get("21K"):
            pound_sell = round(karats["21K"]["sell_price"] * 8.0, 2)
            pound_buy = round(karats["21K"]["buy_price"] * 8.0, 2)

        # Dealer quotes breakdown
        dealers = []
        for s in g21.get("sellers", []):
            dealers.append({
                "seller": s.get("seller"),
                "seller_ar": s.get("sellerAr") or s.get("seller"),
                "karat": "21K",
                "buy": float(s.get("buy") or 0.0),
                "sell": float(s.get("sell") or 0.0),
            })

        # Global reference indicators
        global_gold_usd = g24.get("global", {}).get("value")
        usd_rate = usd_asset.get("benchmark", {}).get("sell") or usd_asset.get("directions", {}).get("sell", {}).get("best", {}).get("value")

        return {
            "status": "live" if is_fresh else "delayed",
            "provider": "Daleelak (getdaleelak.com)",
            "provider_url": "https://getdaleelak.com/ar/api",
            "license": "Free to use with attribution to getdaleelak.com",
            "attribution": "بيانات الأسعار مقدمة مجاناً من دليلـك (getdaleelak.com)",
            "generated_at": generated_at,
            "observed_at": observed_at,
            "retrieved_at": now_utc.isoformat(),
            "currency": "EGP",
            "karats": karats,
            "gold_pound": {
                "name": "Gold Sovereign / Egyptian Gold Pound",
                "name_ar": "جنيه الذهب المصري (8 جرام عيار 21)",
                "sell_price": float(pound_sell or 0.0),
                "buy_price": float(pound_buy or 0.0),
                "weight_g": 8.00,
                "karat": "21K"
            },
            "dealers": dealers[:6],
            "indicators": {
                "usd_egp": float(usd_rate or 55.30),
                "global_xau_usd": float(global_gold_usd or 2740.0)
            }
        }

    @classmethod
    def _parse_goldpricestoday_feed(cls, feed: Dict[str, Any], now_utc: datetime) -> Dict[str, Any]:
        updated_at = feed.get("updated", now_utc.isoformat())
        prices = feed.get("prices", {})

        karats: Dict[str, Any] = {}
        for karat_key, info in prices.items():
            k_name = f"{karat_key}K"
            if k_name in KARAT_PURITIES and isinstance(info, dict):
                gram_price = round(float(info.get("gram", 0.0)), 2)
                # Estimate standard Sagha buy-back spread if explicit buy is absent
                spread = 35.0 if k_name == "21K" else (40.0 if k_name == "18K" else 25.0)
                buy_val = max(0.0, round(gram_price - spread, 2))

                karats[k_name] = {
                    "karat": k_name,
                    "purity_pct": KARAT_PURITIES[k_name]["purity_pct"],
                    "sell_price": gram_price,
                    "buy_price": buy_val,
                    "spread": spread,
                    "source": "goldpricestoday.net",
                    "best_seller": "Egyptian Gold Market Benchmark",
                    "observed_at": updated_at,
                    "is_indicative": False if k_name in ["24K", "21K", "18K"] else True,
                    "movement": {"change_egp": 0.0, "change_pct": 0.0, "direction": "flat"}
                }

        k21 = karats.get("21K", {})
        pound_sell = round(k21.get("sell_price", 0.0) * 8.0, 2)
        pound_buy = round(k21.get("buy_price", 0.0) * 8.0, 2)

        return {
            "status": "live",
            "provider": "GoldPricesToday (goldpricestoday.net)",
            "provider_url": "https://goldpricestoday.net/developers/",
            "license": "Free with visible link to goldpricestoday.net",
            "attribution": "بيانات الأسعار بالتعاون مع سعر الذهب اليوم (goldpricestoday.net)",
            "generated_at": updated_at,
            "observed_at": updated_at,
            "retrieved_at": now_utc.isoformat(),
            "currency": "EGP",
            "karats": karats,
            "gold_pound": {
                "name": "Gold Sovereign / Egyptian Gold Pound",
                "name_ar": "جنيه الذهب المصري (8 جرام عيار 21)",
                "sell_price": pound_sell,
                "buy_price": pound_buy,
                "weight_g": 8.00,
                "karat": "21K"
            },
            "dealers": [],
            "indicators": {
                "usd_egp": float(feed.get("fx", {}).get("rate", 55.30)),
                "global_xau_usd": float(feed.get("spotUsdPerOunce", 2740.0))
            }
        }

    @classmethod
    def _update_movement_and_cache(cls, current: Dict[str, Any], now_utc: datetime):
        prev = _FEED_CACHE["previous_snapshot"]
        if prev and isinstance(prev.get("karats"), dict):
            prev_karats = prev["karats"]
            for k, cur_data in current.get("karats", {}).items():
                if k in prev_karats:
                    prev_sell = prev_karats[k].get("sell_price", 0.0)
                    cur_sell = cur_data.get("sell_price", 0.0)
                    diff = round(cur_sell - prev_sell, 2)
                    pct = round((diff / prev_sell * 100), 2) if prev_sell > 0 else 0.0
                    direction = "up" if diff > 0 else ("down" if diff < 0 else "flat")
                    cur_data["movement"] = {
                        "change_egp": diff,
                        "change_pct": pct,
                        "direction": direction
                    }

        _FEED_CACHE["previous_snapshot"] = dict(current)
        _FEED_CACHE["last_valid_data"] = dict(current)
        _FEED_CACHE["last_retrieved_at"] = now_utc.isoformat()

    @classmethod
    def _persist_snapshots_to_db(cls, db: Session, data: Dict[str, Any]):
        """Persists snapshots to GoldPrice DB table without duplicate records"""
        try:
            karats = data.get("karats", {})
            for k, info in karats.items():
                sell_price = Decimal(str(info["sell_price"]))
                buy_price = Decimal(str(info["buy_price"]))
                # Check current record
                existing = db.query(GoldPrice).filter(GoldPrice.karat == k, GoldPrice.is_current == True).first()
                if existing:
                    # Only insert a new record if the price has genuinely changed
                    if existing.price_per_gram == sell_price and existing.spread_buy == buy_price:
                        continue
                    existing.is_current = False

                gp = GoldPrice(
                    karat=k,
                    purity_pct=Decimal(str(info["purity_pct"])),
                    price_per_gram=sell_price,
                    spread_sell=Decimal(str(info.get("spread", 0.0))),
                    spread_buy=buy_price,
                    source=info.get("source", "MARKET_FEED"),
                    is_current=True,
                    effective_at=datetime.now(timezone.utc)
                )
                db.add(gp)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to record gold feed snapshot to database: {e}")

    @classmethod
    def _create_offline_mock_data(cls, now_utc: datetime) -> Dict[str, Any]:
        """Provides graceful fallback values when internet is completely disconnected on startup"""
        return {
            "status": "offline",
            "provider": "Unverified (Offline)",
            "provider_url": "",
            "license": "",
            "attribution": "المنظومة غير متصلة بالإنترنت حالياً ولا توجد بيانات أسعار معتمدة مؤقتة.",
            "warning": "تعذر جلب أسعار الذهب اللحظية. يرجى التحقق من اتصال الإنترنت أو إعداد مزود الأسعار من لوحة الإدارة.",
            "generated_at": None,
            "observed_at": None,
            "retrieved_at": now_utc.isoformat(),
            "currency": "EGP",
            "is_stale": True,
            "karats": {},
            "gold_pound": None,
            "dealers": [],
            "indicators": {}
        }

