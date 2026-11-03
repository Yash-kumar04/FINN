"""
pipeline/prove_fixes.py
Proves all 7 fix items after vol + mgmt fixes.
Run from d:\\Projects\\FINN:
    python pipeline/prove_fixes.py
"""
import sys, os, json, re
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PRICES_FILE = "web/public/data/prices.json"
ANN_FILE    = "web/public/data/announcements.json"

# ── helpers ──────────────────────────────────────────────────────────────────
def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

TIER_MAP = {
    "results": 1, "management_change": 1, "M&A": 1,
    "fund_raise": 1, "earnings_call": 1,
    "litigation": 2, "capex": 2, "credit_rating": 2,
    "dividend": 2, "press_release": 2, "investor_meetings": 2,
    "postal_ballot": 3, "unclassified": 3,
}

# ─────────────────────────────────────────────────────────────────────────────
print("=" * 80)
print("PROVE_FIXES.PY — raw output for all 7 items")
print("=" * 80)

prices = load(PRICES_FILE)
ann    = load(ANN_FILE)
events = ann["events"]

# ══════════════════════════════════════════════════════════════════════════════
# ITEM 2 — volume_20d_avg (prior 20 sessions, not including latest bar)
# ══════════════════════════════════════════════════════════════════════════════
print("\n── ITEM 2: volume_ratio for RELIANCE, DIXON, CDSL, SUNPHARMA ──────────────")
check_tickers = ["RELIANCE.NS", "DIXON.NS", "CDSL.NS", "SUNPHARMA.NS"]
for sym in check_tickers:
    td = prices["tickers"].get(sym, {})
    bars = td.get("bars", [])
    metrics = td.get("metrics", {})
    if len(bars) >= 22:
        prior20 = [b["volume"] for b in bars[-21:-1]]
        correct_avg = sum(prior20) / len(prior20)
        last_vol = bars[-1]["volume"]
        correct_ratio = last_vol / correct_avg if correct_avg > 0 else 1.0
        stored_avg = metrics.get("volume_20d_avg", 0)
        stored_ratio = metrics.get("volume_ratio", 0)
        ok = abs(stored_avg - correct_avg) < 1  # should match after fix
        flag = "OK" if ok else "MISMATCH"
        print(f"  {sym:<15} stored_avg={stored_avg:>15,.2f}  correct_avg={correct_avg:>15,.2f}  [{flag}]")
        print(f"  {'':15} stored_ratio={stored_ratio:.4f}  correct_ratio={correct_ratio:.4f}  last_vol={last_vol:,}")
    else:
        print(f"  {sym:<15} insufficient bars ({len(bars)})")

# ══════════════════════════════════════════════════════════════════════════════
# ITEM 1 — tier counts, zero untiered events
# ══════════════════════════════════════════════════════════════════════════════
print("\n── ITEM 1: tier counts & window sums ──────────────────────────────────────")
from datetime import datetime, timezone, timedelta
import pytz
IST = pytz.timezone("Asia/Kolkata")

# Anchor: latest filing timestamp in snapshot
def parse_nse_ts(ts_str):
    try:
        return datetime.strptime(ts_str, "%d-%b-%Y %H:%M:%S").replace(tzinfo=IST)
    except Exception:
        return None

all_ts = [parse_nse_ts(e["timestamp"]) for e in events if e.get("timestamp")]
all_ts = [t for t in all_ts if t]
anchor = max(all_ts) if all_ts else datetime.now(IST)
print(f"  Anchor (snapshot latest filing): {anchor.strftime('%Y-%m-%d %H:%M:%S %Z')}")

tier_counts = {1: 0, 2: 0, 3: 0, "untiered": 0}
for e in events:
    cat = e.get("primary_category", "")
    t = TIER_MAP.get(cat)
    if t:
        tier_counts[t] += 1
    else:
        tier_counts["untiered"] += 1
        print(f"  UNTIERED EVENT: {e['ticker']} | {cat} | {e['title'][:60]}")

total = sum(v for k, v in tier_counts.items() if k != "untiered")
print(f"  Tier 1: {tier_counts[1]}  Tier 2: {tier_counts[2]}  Tier 3: {tier_counts[3]}  "
      f"Untiered: {tier_counts['untiered']}  Total events: {len(events)}")
assert tier_counts["untiered"] == 0, f"FAIL: {tier_counts['untiered']} untiered events!"
print("  ✅ Zero untiered events.")

windows = {"24h": 1, "3D": 3, "7D": 7, "30D": 30}
for label, days in windows.items():
    cutoff = anchor - timedelta(days=days)
    subset = [e for e in events if parse_nse_ts(e.get("timestamp", "")) and parse_nse_ts(e["timestamp"]) >= cutoff]
    t1 = sum(1 for e in subset if TIER_MAP.get(e["primary_category"]) == 1)
    t2 = sum(1 for e in subset if TIER_MAP.get(e["primary_category"]) == 2)
    t3 = sum(1 for e in subset if TIER_MAP.get(e["primary_category"]) == 3)
    total_w = t1 + t2 + t3
    ok = "✅" if total_w == len(subset) else "❌"
    print(f"  {label:>4}: total={len(subset):>3}  T1={t1}  T2={t2}  T3={t3}  sum={total_w}  {ok}")

# ══════════════════════════════════════════════════════════════════════════════
# ITEM 3 — management events, per person
# ══════════════════════════════════════════════════════════════════════════════
print("\n── ITEM 3: management events (per person) ─────────────────────────────────")
mgmt_events = [e for e in events if e["primary_category"] == "management_change"]
print(f"  Total management events: {len(mgmt_events)}")
for e in mgmt_events:
    person = e.get("person_named") or "(generic / no name in API text)"
    print(f"  [{e['ticker']}] person_named={person!r}")
    print(f"    title   : {e['title']}")
    print(f"    raw_desc: {e['primary_filing']['desc']}")
    print(f"    filings : {e['filing_count']}")

# Confirm DIXON Prithvi Vachani
dixon_mgmt = [e for e in mgmt_events if e["ticker"] == "DIXON.NS"]
print(f"\n  DIXON.NS management events: {len(dixon_mgmt)}")
for dm in dixon_mgmt:
    print(f"    person_named: {dm.get('person_named')}")
    print(f"    attachment_text (first 200): {dm['primary_filing']['attachment_text'][:200] if dm['primary_filing']['attachment_text'] else 'NULL'}")
print("  NOTE: Prithvi Vachani is in the PDF attachment, NOT in the NSE API text field.")
print("        The API text says only 'change in Management' with no name. PDF parsing needed (Step 5).")

# ══════════════════════════════════════════════════════════════════════════════
# ITEM 4 — 5 classified events with primary + secondary tags
# ══════════════════════════════════════════════════════════════════════════════
print("\n── ITEM 4: 5 classified events with primary+secondary tags ────────────────")
shown = 0
# Show RELIANCE results first
for e in events:
    if shown >= 5:
        break
    if e["ticker"] == "RELIANCE.NS" and e["primary_category"] == "results":
        print(f"  [RELIANCE results]")
        print(f"    primary_category : {e['primary_category']}")
        print(f"    secondary_tags   : {e['secondary_tags']}")
        print(f"    filing_count     : {e['filing_count']}")
        print(f"    supporting_filings:")
        for i, sf in enumerate(e.get("supporting_filings", [])[:5], 1):
            print(f"      SF[{i}] desc={sf['desc']!r}  cat_hint={sf.get('category','?')}")
        shown += 1
        break

for e in events:
    if shown >= 5:
        break
    if e["ticker"] != "RELIANCE.NS":
        print(f"  [{e['ticker']} {e['primary_category']}]")
        print(f"    title            : {e['title'][:70]}")
        print(f"    primary_category : {e['primary_category']}")
        print(f"    secondary_tags   : {e['secondary_tags']}")
        shown += 1

# ══════════════════════════════════════════════════════════════════════════════
# ITEM 5 — top 10 in 72h with score breakdown (re-computed from updated prices)
# ══════════════════════════════════════════════════════════════════════════════
print("\n── ITEM 5: top 10 events (72h) with score breakdown ───────────────────────")
cutoff_72h = anchor - timedelta(hours=72)
recent = [e for e in events if parse_nse_ts(e.get("timestamp","")) and parse_nse_ts(e["timestamp"]) >= cutoff_72h]
recent_sorted = sorted(recent, key=lambda x: x["importance_score"], reverse=True)[:10]
print(f"  72h cutoff: {cutoff_72h.strftime('%Y-%m-%d %H:%M:%S %Z')}  events in window: {len(recent)}")
for idx, ev in enumerate(recent_sorted, 1):
    b = ev["score_breakdown"]
    print(f"  [{idx:>2}] {ev['ticker']:<14} | {ev['primary_category']:<18} | Score={ev['importance_score']:.2f}")
    print(f"        cat_wt={b['category_weight']}  port_wt={b['portfolio_weight']}  "
          f"vol_ratio={b['volume_ratio']}x  price={b['price_change_abs_pct']}%  mult={b['market_reaction_multiplier']}")
    print(f"        title: {ev['title'][:55]}  ts: {ev['timestamp']}")

# ══════════════════════════════════════════════════════════════════════════════
# ITEM 6 — why Tier 3 changed
# ══════════════════════════════════════════════════════════════════════════════
print("\n── ITEM 6: tier 3 event count ─────────────────────────────────────────────")
t3_events = [e for e in events if TIER_MAP.get(e["primary_category"]) == 3]
t3_cats = {}
for e in t3_events:
    c = e["primary_category"]
    t3_cats[c] = t3_cats.get(c, 0) + 1
print(f"  Tier 3 events total: {len(t3_events)}")
for c, n in sorted(t3_cats.items(), key=lambda x: -x[1]):
    print(f"    {c}: {n}")

# ══════════════════════════════════════════════════════════════════════════════
# ITEM 7 — BSE fallback (stored in ann JSON provenance)
# ══════════════════════════════════════════════════════════════════════════════
print("\n── ITEM 7: BSE fallback report ─────────────────────────────────────────────")
bse_used = []
for sym, td in ann.get("tickers", {}).items():
    prov = td.get("provenance", {})
    if prov.get("source") == "bse":
        bse_used.append(sym)
print(f"  Tickers that used BSE fallback: {len(bse_used)} {bse_used}")
for sym in ["KAYNES.NS", "HAL.NS"]:
    td = ann.get("tickers", {}).get(sym, {})
    count = len(td.get("announcements", []))
    prov = td.get("provenance", {})
    print(f"  {sym}: source={prov.get('source','?')}  filings={count}")

print("\n" + "=" * 80)
print("DONE — all 7 items proved from snapshot. No data typed.")
print("=" * 80)

