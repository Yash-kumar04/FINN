import sys, json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

with open("web/public/data/announcements.json", encoding="utf-8") as f:
    ann = json.load(f)

# =========================================================================
# ITEM 4: 5 classified events with primary + secondary tags
# =========================================================================
print("=" * 80)
print("ITEM 4: 5 CLASSIFIED EVENTS — PRIMARY + SECONDARY TAGS")
print("=" * 80)

# Specifically show RELIANCE transcript filing and RELIANCE investor presentation
reliance_events = [e for e in ann["events"] if e.get("ticker") == "RELIANCE.NS"]
print(f"RELIANCE.NS has {len(reliance_events)} events total")

# Find transcript-related events (from supporting filings)
print("\n--- RELIANCE Results Event (contains transcript + presentation filings) ---")
for ev in reliance_events:
    if ev["primary_category"] == "results":
        print(f"event_id: {ev['event_id']}")
        print(f"primary_category: {ev['primary_category']}")
        print(f"secondary_tags: {ev['secondary_tags']}")
        print(f"title: {ev['title']}")
        print(f"filing_count: {ev['filing_count']}")
        print(f"Primary filing: [{ev['primary_filing']['desc']}]")
        for j, sf in enumerate(ev.get("supporting_filings", []), 1):
            print(f"  SF[{j}]: [{sf.get('category')}] desc={sf.get('desc')}")
            print(f"       text[:120]: {(sf.get('attachment_text') or '')[:120]}")
        break

print("\n--- 5 Sample Events across categories with primary + secondary tags ---")
shown_cats = set()
count = 0
for ev in ann["events"]:
    cat = ev["primary_category"]
    if cat not in shown_cats or count < 5:
        shown_cats.add(cat)
        print(f"\n[{count+1}] {ev['ticker']} | primary={ev['primary_category']} | secondary={ev['secondary_tags']}")
        print(f"     title: {ev['title'][:60]}")
        print(f"     desc:  {ev['primary_filing']['desc']}")
        print(f"     score: {ev['importance_score']}")
        count += 1
        if count >= 5:
            break

# =========================================================================
# ITEM 5: Importance score formula + top 10 in 72h
# =========================================================================
print("\n" + "=" * 80)
print("ITEM 5: IMPORTANCE SCORE FORMULA, PORTFOLIO WEIGHTS, TOP 10 IN 72H")
print("=" * 80)

print("""
FORMULA (from classifier.py CATEGORY_WEIGHTS and build_step1b.py):
  Score = Category_Weight × Portfolio_Weight × Market_Reaction_Multiplier × 100

  Category_Weight:
    results=1.0, management_change=0.9, M&A=0.9, fund_raise=0.85, litigation=0.8, capex=0.75
    credit_rating=0.65, dividend=0.6, bonus_split=0.6, insider_trading=0.55
    earnings_call=0.5, press_release=0.45, investor_meetings=0.35
    postal_ballot=0.3, agm_egm=0.3, pledging=0.4, unclassified=0.1

  Market_Reaction_Multiplier = 1.0
    + min(max(vol_ratio - 1.0, 0), 3.0) × 0.15
    + min(|price_change_pct|, 10.0) × 0.05

  Note: vol_ratio currently uses avg of last 20 bars INCLUDING the latest bar.
        BUG will be fixed (Item 2): should use prior 20 sessions only.
""")

print("PORTFOLIO WEIGHTS:")
with open("web/public/data/prices.json", encoding="utf-8") as f:
    prices = json.load(f)
for sym, t in prices["tickers"].items():
    print(f"  {sym:<18} {t['name']:<30} weight={t['portfolio_weight']:.2f}")

from datetime import datetime, timedelta
def parse_ts(ts):
    if not ts:
        return None
    try:
        return datetime.strptime(ts, "%d-%b-%Y %H:%M:%S")
    except Exception:
        return None

events = ann["events"]
anchor_dt = max((parse_ts(e.get("timestamp")) for e in events if parse_ts(e.get("timestamp"))), default=None)
cutoff_72h = anchor_dt - timedelta(hours=72)

recent = [e for e in events if (parse_ts(e.get("timestamp")) or anchor_dt) >= cutoff_72h]
recent.sort(key=lambda x: x.get("importance_score", 0), reverse=True)

print(f"\nTOP 10 EVENTS IN 72H WINDOW (cutoff={cutoff_72h}, anchor={anchor_dt}):")
for i, ev in enumerate(recent[:10], 1):
    b = ev.get("score_breakdown", {})
    print(f"\n[{i}] {ev['ticker']:<14} | {ev['primary_category']:<20} | Score={ev['importance_score']:.2f}")
    print(f"     title: {ev['title'][:60]}")
    print(f"     cat_wt={b.get('category_weight')} | port_wt={b.get('portfolio_weight')} | vol_ratio={b.get('volume_ratio')} | price_chg={b.get('price_change_abs_pct')}% | multiplier={b.get('market_reaction_multiplier')}")
    print(f"     timestamp: {ev['timestamp']} | filing_count={ev['filing_count']}")
    print(f"     why_you_should_care: {ev.get('why_you_should_care')}")

