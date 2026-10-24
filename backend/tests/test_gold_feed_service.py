import pytest
from datetime import datetime, timezone
from app.services.gold_feed_service import GoldFeedService

SAMPLE_DALEELAK_FEED = {
    "schemaVersion": 1,
    "generatedAt": "2026-10-24T12:00:37.079Z",
    "assets": [
        {
            "id": "GOLD24K-EGP",
            "slug": "gold-24k",
            "category": "metals",
            "kind": "metal",
            "unit": "EGP/g",
            "observedAt": "2026-10-24T12:00:00.000Z",
            "freshness": {"state": "fresh", "stale": False},
            "directions": {
                "sell": {"best": {"seller": "Gold Bullion EG", "value": 7143.0}},
                "buy": {"best": {"seller": "BTC", "value": 7160.39}}
            },
            "sellers": [
                {"seller": "BTC", "buy": 7081.87, "sell": 7160.39},
                {"seller": "Gold Bullion EG", "buy": 7143.0, "sell": 7166.0}
            ],
            "global": {"value": 2740.50}
        },
        {
            "id": "GOLD21K-EGP",
            "slug": "gold-21k",
            "category": "metals",
            "kind": "metal",
            "unit": "EGP/g",
            "observedAt": "2026-10-24T12:00:00.000Z",
            "freshness": {"state": "fresh", "stale": False},
            "directions": {
                "sell": {"best": {"seller": "Gold Bullion EG", "value": 6250.0}},
                "buy": {"best": {"seller": "BTC", "value": 6230.0}}
            },
            "sellers": [
                {"seller": "BTC", "buy": 6195.0, "sell": 6265.0},
                {"seller": "Gold Bullion EG", "buy": 6250.0, "sell": 6270.0}
            ]
        },
        {
            "id": "GOLD18K-EGP",
            "slug": "gold-18k",
            "category": "metals",
            "kind": "metal",
            "unit": "EGP/g",
            "observedAt": "2026-10-24T12:00:00.000Z",
            "freshness": {"state": "fresh", "stale": False},
            "directions": {
                "sell": {"best": {"seller": "Gold Bullion EG", "value": 5357.0}},
                "buy": {"best": {"seller": "BTC", "value": 5340.0}}
            }
        },
        {
            "id": "GOLDPOUND-EGP",
            "slug": "gold-pound",
            "category": "metals",
            "kind": "metal",
            "unit": "EGP",
            "directions": {
                "sell": {"best": {"seller": "Gold Bullion EG", "value": 50000.0}},
                "buy": {"best": {"seller": "BTC", "value": 49840.0}}
            }
        },
        {
            "id": "USD-EGP",
            "benchmark": {"sell": 55.30}
        }
    ]
}

def test_parse_daleelak_feed_verified_karats():
    now = datetime.now(timezone.utc)
    parsed = GoldFeedService._parse_daleelak_feed(SAMPLE_DALEELAK_FEED, now)

    assert parsed["status"] == "live"
    assert parsed["provider"] == "Daleelak (getdaleelak.com)"
    karats = parsed["karats"]

    # 24K, 21K, 18K must be verified quotes
    assert karats["24K"]["sell_price"] == 7143.0
    assert karats["24K"]["is_indicative"] is False
    assert karats["21K"]["sell_price"] == 6250.0
    assert karats["21K"]["is_indicative"] is False
    assert karats["18K"]["sell_price"] == 5357.0
    assert karats["18K"]["is_indicative"] is False

    # 22K, 14K, 12K must be derived and explicitly labelled indicative
    assert karats["22K"]["is_indicative"] is True
    assert "Indicative" in karats["22K"]["source"]
    assert karats["14K"]["is_indicative"] is True
    assert karats["12K"]["is_indicative"] is True

    # Gold Pound 8g
    assert parsed["gold_pound"]["sell_price"] == 50000.0
    assert parsed["gold_pound"]["weight_g"] == 8.00

def test_movement_calculation():
    now = datetime.now(timezone.utc)
    initial = GoldFeedService._parse_daleelak_feed(SAMPLE_DALEELAK_FEED, now)
    GoldFeedService._update_movement_and_cache(initial, now)

    # Modify prices to simulate higher market quote
    updated_feed = dict(SAMPLE_DALEELAK_FEED)
    updated_feed["assets"] = [dict(a) for a in SAMPLE_DALEELAK_FEED["assets"]]
    updated_feed["assets"][1]["directions"]["sell"]["best"]["value"] = 6275.0 # +25 EGP

    updated = GoldFeedService._parse_daleelak_feed(updated_feed, now)
    GoldFeedService._update_movement_and_cache(updated, now)

    k21_movement = updated["karats"]["21K"]["movement"]
    assert k21_movement["change_egp"] == 25.0
    assert k21_movement["direction"] == "up"
    assert k21_movement["change_pct"] > 0

def test_live_feed_api_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/pricing/live-feed")
    assert response.status_code == 200
    data = response.json()
    assert "karats" in data
    assert "21K" in data["karats"]
    assert "24K" in data["karats"]
    assert "gold_pound" in data
    assert "provider" in data

