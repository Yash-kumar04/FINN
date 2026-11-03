import json

prices = json.load(open('web/public/data/prices.json', encoding='utf-8'))
tickers = ['RELIANCE.NS', 'DIXON.NS', 'CDSL.NS', 'SUNPHARMA.NS']

print("=" * 80)
print("ITEM 1: LAST 3 RAW BARS (ENDING AT 2026-11-02, NO 2026-11-03 BAR)")
print("=" * 80)

for sym in tickers:
    td = prices['tickers'][sym]
    prov = td['provenance']
    bars = td['bars']
    print(f"Ticker: {sym} | as_of_date: {prov['as_of_date']} | fetched_at_ist: {prov['fetched_at_ist']}")
    print(f"Total bars in snapshot: {len(bars)}")
    for b in bars[-3:]:
        print(f"  Date: {b['date']} | Open: {b['open']} | High: {b['high']} | Low: {b['low']} | Close: {b['close']} | Volume: {b['volume']:,} | Provisional: {b['provisional']}")
    print()

