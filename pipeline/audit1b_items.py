import sys, json
from collections import Counter
from datetime import datetime, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

with open("web/public/data/announcements.json", encoding="utf-8") as f:
    ann = json.load(f)

with open("web/public/data/prices.json", encoding="utf-8") as f:
    prices = json.load(f)

TIER1_CATS = {"results", "management_change", "M&A", "fund_raise", "litigation", "capex"}
TIER2_CATS = {"credit_rating", "dividend", "bonus_split", "insider_trading",
              "earnings_call", "press_release", "investor_meetings"}
TIER3_CATS = {"unclassified", "postal_ballot", "agm_egm", "pledging"}

events = ann["events"]

# =========================================================================
# ITEM 1: Tier accounting
# =========================================================================
print("=" * 80)
print("ITEM 1: TIER ACCOUNTING")
print("=" * 80)

def get_tier(cat):
    if cat in TIER1_CATS:
        return 1
    elif cat in TIER2_CATS:
        return 2
    elif cat in TIER3_CATS:
        return 3
    else:
        return None

no_tier = []
for ev in events:
    cat = ev.get("primary_category")
    t = get_tier(cat)
    if t is None:
        no_tier.append(ev)

print(f"Total events: {len(events)}")
print(f"Events with no recognized tier (None): {len(no_tier)}")
for ev in no_tier:
    print(f"  event_id={ev['event_id']} | ticker={ev['ticker']} | primary_category={ev['primary_category']}")

tier_counts = Counter(get_tier(e.get("primary_category")) for e in events)
print(f"\nAll events tier distribution: {dict(sorted(tier_counts.items()))}")

# 30D window counts
def parse_ts(ts):
    if not ts:
        return None
    try:
        return datetime.strptime(ts, "%d-%b-%Y %H:%M:%S")
    except Exception:
        return None

anchor_dt = max((parse_ts(e.get("timestamp")) for e in events if parse_ts(e.get("timestamp"))), default=None)
print(f"\nSnapshot anchor DT: {anchor_dt}")

for label, hours in [("24h", 24), ("3D", 72), ("7D", 168), ("30D", 720)]:
    cutoff = anchor_dt - timedelta(hours=hours)
    in_win = [e for e in events if (parse_ts(e.get("timestamp")) or anchor_dt) >= cutoff]
    t1 = [e for e in in_win if get_tier(e["primary_category"]) == 1]
    t2 = [e for e in in_win if get_tier(e["primary_category"]) == 2]
    t3 = [e for e in in_win if get_tier(e["primary_category"]) == 3]
    tn = [e for e in in_win if get_tier(e["primary_category"]) is None]
    total = len(in_win)
    sum_tiers = len(t1) + len(t2) + len(t3) + len(tn)
    print(f"  Window {label:>4}: {total:3d} events | T1={len(t1):2d} T2={len(t2):2d} T3={len(t3):2d} None={len(tn):2d} | sum={sum_tiers}")

