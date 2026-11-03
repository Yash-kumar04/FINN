import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open('web/public/data/prices.json', encoding='utf-8') as f:
    p = json.load(f)

print("=== LAST 3 BARS RAW (from existing snapshot) ===")
for sym in ['RELIANCE.NS', 'DIXON.NS', 'TRENT.NS']:
    t = p['tickers'][sym]
    bars = t['bars']
    print(f"\n--- {sym} ({t['name']}) ---")
    for b in bars[-3:]:
        print(f"  date={b['date']}  open={b['open']}  high={b['high']}  low={b['low']}  close={b['close']}  volume={b['volume']}  provisional={b['provisional']}")
    m = t['metrics']
    print(f"  metrics: last_close={m['last_close']}  price_change_pct={m['price_change_pct']:+.6f}%  volume_ratio={m['volume_ratio']:.6f}")
    print(f"  as_of={t['provenance']['as_of_date']}  fetched_at_ist={t['provenance']['fetched_at_ist']}")

print(f"\nSnapshot-level as_of_date: {p['provenance']['as_of_date']}")
print(f"Snapshot fetched_at_ist:   {p['provenance']['fetched_at_ist']}")

