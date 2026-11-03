import sys, json
from collections import Counter
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

with open("web/public/data/prices.json", encoding="utf-8") as f:
    prices = json.load(f)

with open("web/public/data/announcements.json", encoding="utf-8") as f:
    ann = json.load(f)

# =========================================================================
# ITEM 2: volume_20d_avg calculation — does it include the latest day?
# =========================================================================
print("=" * 80)
print("ITEM 2: VOLUME_20D_AVG CALCULATION AUDIT")
print("=" * 80)

for sym in ["RELIANCE.NS", "DIXON.NS", "CDSL.NS", "SUNPHARMA.NS"]:
    t = prices["tickers"][sym]
    bars = t["bars"]
    m = t["metrics"]
    
    # Current calculation in fetch_prices.py:
    # vol_20d = [b["volume"] for b in bars[-20:]]  # INCLUDES the last bar
    # avg_vol_20d = sum(vol_20d) / len(vol_20d)
    
    # Correct: prior 20 sessions (exclude last bar)
    last_bar = bars[-1]
    prior_bars = bars[-21:-1]  # 20 bars before the last
    
    current_avg = sum(b["volume"] for b in bars[-20:]) / min(20, len(bars[-20:]))
    correct_avg = sum(b["volume"] for b in prior_bars) / len(prior_bars) if prior_bars else last_bar["volume"]
    
    current_ratio = last_bar["volume"] / current_avg if current_avg > 0 else 0
    correct_ratio = last_bar["volume"] / correct_avg if correct_avg > 0 else 0
    
    stored_ratio = m["volume_ratio"]
    stored_avg = m["volume_20d_avg"]
    
    print(f"\n{sym}:")
    print(f"  Last bar: date={last_bar['date']}, volume={last_bar['volume']:,}")
    print(f"  Stored  volume_20d_avg: {stored_avg:,.2f}  (INCLUDES last day?: {'YES - BUG' if abs(stored_avg - current_avg) < 1 else 'NO - OK'})")
    print(f"  Current calc (incl. last): avg={current_avg:,.2f}, ratio={current_ratio:.4f}")
    print(f"  Correct calc (prior 20):   avg={correct_avg:,.2f}, ratio={correct_ratio:.4f}")
    print(f"  Stored vol_ratio in JSON:  {stored_ratio:.4f}")
    
    if abs(stored_ratio - current_ratio) < 0.0001:
        print(f"  => Stored ratio matches CURRENT (includes latest day) -- BUG CONFIRMED")
    elif abs(stored_ratio - correct_ratio) < 0.0001:
        print(f"  => Stored ratio matches CORRECT (prior 20) -- OK")
    else:
        print(f"  => Stored ratio matches neither -- investigate")

