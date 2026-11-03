import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open('web/public/data/prices.json', encoding='utf-8') as f:
    p = json.load(f)
with open('web/public/data/announcements.json', encoding='utf-8') as f:
    a = json.load(f)

print("=== ALERT SIMULATION (default thresholds: price>=3%, vol>=2.0x) ===")
PRICE_THR = 3.0
VOL_THR = 2.0
price_alerts = []
vol_alerts = []
for sym, t in p['tickers'].items():
    m = t['metrics']
    chg = m['price_change_pct']
    vr  = m['volume_ratio']
    if abs(chg) >= PRICE_THR:
        price_alerts.append((sym, chg, vr))
    if vr >= VOL_THR:
        vol_alerts.append((sym, chg, vr))

price_alerts.sort(key=lambda x: abs(x[1]), reverse=True)
vol_alerts.sort(key=lambda x: x[2], reverse=True)

print(f"\nPrice alerts fired (|chg| >= {PRICE_THR}%): {len(price_alerts)}")
for sym, chg, vr in price_alerts:
    print(f"  {sym:<18} chg={chg:+.2f}%  vol_ratio={vr:.2f}x")

print(f"\nVolume alerts fired (vol >= {VOL_THR}x): {len(vol_alerts)}")
for sym, chg, vr in vol_alerts:
    print(f"  {sym:<18} chg={chg:+.2f}%  vol_ratio={vr:.2f}x")

print("\n=== ANNOUNCEMENTS JSON SCHEMA ===")
print(f"Top-level keys: {list(a.keys())}")
print(f"Total events: {len(a.get('events', []))}")
print(f"stats: {a.get('stats', {})}")
print(f"provenance: {a.get('provenance', {})}")

# Check first event field names
ev0 = a['events'][0]
print(f"\nFirst event field names: {list(ev0.keys())}")
print(f"  primary_category: {ev0.get('primary_category')}")
print(f"  ticker: {ev0.get('ticker')}")
print(f"  title: {ev0.get('title')}")
print(f"  timestamp: {ev0.get('timestamp')}")
print(f"  why_you_should_care: {ev0.get('why_you_should_care')}")
print(f"  secondary_tags: {ev0.get('secondary_tags')}")

# Count 245->190 explanation
print("\n=== 245 filings -> 190 events explanation ===")
tickers_data = a.get('tickers', {})
total_filings = sum(len(v.get('announcements', [])) for v in tickers_data.values())
# count events per type
from collections import Counter
ev_cats = Counter(ev.get('primary_category') for ev in a.get('events', []))
print(f"Total raw filings (sum of per-ticker announcements): {total_filings}")
print(f"Total events: {len(a.get('events', []))}")
print(f"Events by category: {dict(ev_cats)}")

# Show which tickers had merging (results cluster > 1 filing)
print("\nTickers with results event (filing_count > 1 = grouped):")
for ev in a.get('events', []):
    if ev.get('primary_category') == 'results' and ev.get('filing_count', 0) > 1:
        print(f"  {ev['ticker']:<16} {ev['filing_count']} filings -> 1 results event (saved {ev['filing_count']-1})")

