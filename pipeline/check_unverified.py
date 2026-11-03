import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json

ann = json.load(open('web/public/data/announcements.json', encoding='utf-8'))
for ev in ann['events']:
    ticker = ev.get('ticker')
    if ticker in ['M&M.NS', 'TITAN.NS', 'MARUTI.NS', 'TRENT.NS', 'BAJAJ-AUTO.NS']:
        print(f"=== {ticker} ({ev.get('primary_category')}) ===")
        pf = ev.get('primary_filing', {})
        print(f"  PF URL: {pf.get('attachment_url')}")
        print(f"  PF Desc: {pf.get('desc') or pf.get('raw_desc')}")
        for sf in ev.get('supporting_filings', []):
            print(f"  SF URL: {sf.get('attachment_url')}")
            print(f"  SF Desc: {sf.get('desc') or sf.get('raw_desc')}")

