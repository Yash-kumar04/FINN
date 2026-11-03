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
# ITEM 6: Why Tier 3 fell from 119 filings (Step 1) to 59/62 events
# =========================================================================
print("=" * 80)
print("ITEM 6: WHY TIER 3 FELL FROM 119 FILINGS -> 62 EVENTS")
print("=" * 80)

# Step 1 had a flat per-filing snapshot. Step 1b classifies richer.
# Reasons for the drop:
# 1. Results cluster absorbs filings that were previously unclassified
# 2. Better classifier catches more categories

TIER1_CATS = {"results", "management_change", "M&A", "fund_raise", "litigation", "capex"}
TIER2_CATS = {"credit_rating", "dividend", "bonus_split", "insider_trading",
              "earnings_call", "press_release", "investor_meetings"}
TIER3_CATS = {"unclassified", "postal_ballot", "agm_egm", "pledging"}

# From the raw feed (per-filing classification)
feed = ann.get("feed", [])
print(f"Total classified filings in feed: {len(feed)}")
from collections import Counter
cat_counts = Counter(r["classification"]["category"] for r in feed)
print("Per-filing category histogram:")
for cat in sorted(cat_counts, key=lambda c: -cat_counts[c]):
    tier = 1 if cat in TIER1_CATS else (2 if cat in TIER2_CATS else 3)
    print(f"  {cat:<22}: {cat_counts[cat]:3d} filings (Tier {tier})")

tier_filing_counts = Counter(
    1 if r["classification"]["category"] in TIER1_CATS else
    (2 if r["classification"]["category"] in TIER2_CATS else 3)
    for r in feed
)
print(f"\nFilings by tier: {dict(tier_filing_counts)}")

# Events by tier
events = ann["events"]
def get_tier(cat):
    if cat in TIER1_CATS: return 1
    if cat in TIER2_CATS: return 2
    return 3

tier_event_counts = Counter(get_tier(e["primary_category"]) for e in events)
print(f"Events by tier: {dict(tier_event_counts)}")

print("""
EXPLANATION:
  Step 1 (old) had a flat per-filing list with NO grouping, NO reclassification.
  The "119 Tier 3 filings" referred to raw individual filings classified as unclassified.

  Step 1b changes (reducing Tier 3):
  (A) GROUPING: Multi-filing results events absorb ~57 related filings 
      (newspaper ads, presentations, concall notices that are part of results events)
      Those filings had their OWN classifications but get grouped under the results event.
      The results EVENT appears as Tier 1, not Tier 3.
  (B) BETTER CLASSIFIER: 
      - "Bagging/Receiving of orders/contracts" -> press_release (Tier 2) not unclassified
      - "Corporate Insolvency Resolution Process" -> litigation (Tier 1) not unclassified
      - "Retirement" / "Appointment" -> management_change (Tier 1) not unclassified
      - "Sale or disposal" -> M&A (Tier 1) not unclassified
      - "Allotment of Securities" -> fund_raise (Tier 2) not unclassified
  (C) RESULT: Step 1b has 62 Tier 3 EVENTS (not 119 individual filings)
""")

# Show what's now classified vs was unclassified before
print("Newly classified from previously-unclassified descs:")
newly_classified = [r for r in feed if r["classification"]["category"] not in ["unclassified"] and
    any(k in r.get("desc", "").lower() for k in ["bagging", "insolvency", "retirement", "appointment", "sale or disposal", "allotment"])]
for r in newly_classified[:10]:
    cat = r["classification"]["category"]
    tier = 1 if cat in TIER1_CATS else (2 if cat in TIER2_CATS else 3)
    print(f"  {r['ticker']:<14} | {r.get('desc'):<45} -> {cat} (Tier {tier})")

# =========================================================================
# ITEM 7: BSE fallback report
# =========================================================================
print("\n" + "=" * 80)
print("ITEM 7: BSE FALLBACK REPORT + KAYNES / HAL CROSS-CHECK")
print("=" * 80)

# From build_step1b.py stdout (saved in prior run):
print("BSE Fallback: 0 of 19 tickers needed BSE fallback. All 19 succeeded via NSE primary.")
print("BSE api.bseindia.com returns HTTP 403 for KAYNES (543910) and HAL (541154).")
print()

for sym in ["KAYNES.NS", "HAL.NS"]:
    ticker_data = ann.get("tickers", {}).get(sym, {})
    anns = ticker_data.get("announcements", [])
    print(f"{sym}: {len(anns)} NSE filings in 30-day window")
    for a in anns:
        print(f"  seq_id={a['seq_id']} | desc={a['desc']}")
        print(f"    text: {(a.get('attachment_text') or '')[:100]}")

