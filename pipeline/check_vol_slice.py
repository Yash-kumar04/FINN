import sys, json
sys.stdout.reconfigure(encoding="utf-8")
prices = json.load(open("web/public/data/prices.json", encoding="utf-8"))
# Check RELIANCE volume slicing
td = prices["tickers"]["RELIANCE.NS"]
bars = td["bars"]
print(f"Total bars: {len(bars)}")
print("bars[-21:-1] dates and volumes:")
for b in bars[-21:-1]:
    print(f"  {b['date']}  V={b['volume']:,}")
vol_slice = [b["volume"] for b in bars[-21:-1]]
avg = sum(vol_slice)/len(vol_slice)
last_vol = bars[-1]["volume"]
print(f"\navg of prior 20 = {avg:,.2f}")
print(f"last bar vol    = {last_vol:,}  (date={bars[-1]['date']})")
print(f"vol_ratio       = {last_vol/avg:.4f}")
stored_avg = td["metrics"]["volume_20d_avg"]
stored_ratio = td["metrics"]["volume_ratio"]
print(f"\nstored avg={stored_avg:,.2f}  stored_ratio={stored_ratio:.4f}")
print(f"MATCH: {abs(stored_avg - avg) < 1}")

