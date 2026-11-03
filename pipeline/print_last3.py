import sys, json
sys.stdout.reconfigure(encoding="utf-8")
prices = json.load(open("web/public/data/prices.json", encoding="utf-8"))
for sym in ["RELIANCE.NS", "DIXON.NS", "TRENT.NS"]:
    td = prices["tickers"][sym]
    bars = td["bars"]
    prov = td["provenance"]
    print(f"--- {sym} ---")
    print(f"  fetched_at_ist : {prov['fetched_at_ist']}")
    print(f"  as_of_date     : {prov['as_of_date']}")
    for b in bars[-3:]:
        print(f"  {b['date']}  O={b['open']}  H={b['high']}  L={b['low']}  C={b['close']}  V={b['volume']}  provisional={b['provisional']}")
    m = td["metrics"]
    print(f"  vol_20d_avg={m['volume_20d_avg']:,.2f}  vol_ratio={m['volume_ratio']:.4f}")
    print()

