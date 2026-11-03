import json
from datetime import datetime, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")
def parse_ts(ts_str):
    try:
        return datetime.strptime(ts_str, "%d-%b-%Y %H:%M:%S").replace(tzinfo=IST)
    except:
        return None

CATEGORY_WEIGHTS = {
    "results": 1.0,
    "management_change": 0.9,
    "M&A": 0.9,
    "fund_raise": 0.85,
    "litigation": 0.8,
    "capex": 0.75,
    "credit_rating": 0.65,
    "dividend": 0.6,
    "earnings_call": 0.5,
    "press_release": 0.45,
    "investor_meetings": 0.35,
    "postal_ballot": 0.3,
    "unclassified": 0.1
}

prices_json = json.load(open('web/public/data/prices.json', encoding='utf-8'))
ann_json = json.load(open('web/public/data/announcements.json', encoding='utf-8'))

# Test multiplier formula:
# Multiplier = 1.0 + min(max(vol_ratio - 1.0, 0), 5.0) * 0.25 + min(abs(price_chg), 15.0) * 0.10
def compute_importance_score(cat, p_weight, vol_ratio, price_chg):
    cat_weight = CATEGORY_WEIGHTS.get(cat, 0.1)
    vol_boost = max(vol_ratio - 1.0, 0.0)
    vol_comp = min(vol_boost, 5.0) * 0.25
    price_comp = min(abs(price_chg), 15.0) * 0.10
    multiplier = 1.0 + vol_comp + price_comp
    score = round(cat_weight * p_weight * multiplier * 100.0, 2)
    breakdown = {
        "category_weight": cat_weight,
        "portfolio_weight": p_weight,
        "volume_ratio": round(vol_ratio, 2),
        "price_change_abs_pct": round(abs(price_chg), 2),
        "vol_boost_component": round(vol_comp, 3),
        "price_component": round(price_comp, 3),
        "market_reaction_multiplier": round(multiplier, 3),
        "final_score": score
    }
    return score, breakdown

# Rebuild events with latest filing timestamp and updated formula
from build_step1b import group_ticker_announcements_into_events, PORTFOLIO

portfolio_map = {p["symbol"]: p for p in PORTFOLIO}
all_events = []

for sym, ticker_data in ann_json.get("tickers", {}).items():
    p_info = portfolio_map.get(sym, {"weight": 0.05, "name": sym})
    metrics = prices_json.get("tickers", {}).get(sym, {}).get("metrics", {})
    p_weight = p_info["weight"]
    vol_ratio = metrics.get("volume_ratio", 1.0)
    price_chg = metrics.get("price_change_pct", 0.0)

    # Re-group
    ticker_events = group_ticker_announcements_into_events(sym, ticker_data.get("announcements", []), p_info["name"], p_weight, metrics)
    all_events.extend(ticker_events)

# Find snapshot anchor (max timestamp across all events)
all_ts = [parse_ts(e["timestamp"]) for e in all_events if parse_ts(e.get("timestamp"))]
anchor = max(all_ts)
cutoff_72h = anchor - timedelta(hours=72)

recent_72h = [e for e in all_events if parse_ts(e.get("timestamp")) and parse_ts(e["timestamp"]) >= cutoff_72h]
recent_72h.sort(key=lambda x: x["importance_score"], reverse=True)

print(f"Anchor: {anchor.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"72h Cutoff: {cutoff_72h.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"Total events in 72h window: {len(recent_72h)}")
print("\nTop 10 Events over 72h:")
for i, ev in enumerate(recent_72h[:10], 1):
    b = ev["score_breakdown"]
    print(f"[{i:>2}] {ev['ticker']:<14} | {ev['primary_category']:<18} | Score={ev['importance_score']:.2f}")
    print(f"     title: {ev['title'][:60]}")
    print(f"     timestamp: {ev['timestamp']} | filings: {ev['filing_count']}")
    print(f"     breakdown: cat_wt={b['category_weight']} * port_wt={b['portfolio_weight']} * mult={b['market_reaction_multiplier']} -> {b['final_score']}")
    print(f"     market: vol_ratio={b['volume_ratio']}x, price_chg={b['price_change_abs_pct']}%")
    print()

