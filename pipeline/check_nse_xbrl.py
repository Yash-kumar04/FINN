import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

for sym in ["MARUTI", "BAJAJ-AUTO", "TRENT", "M&M", "TITAN"]:
    url = f"https://www.nseindia.com/api/corporates-financial-results?index=equities&symbol={sym}"
    try:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers, timeout=5)
        r = s.get(url, headers=headers, timeout=5)
        data = r.json()
        print(f"=== {sym} ({len(data)} results) ===")
        if data:
            print("  First item keys:", data[0].keys())
            for item in data[:2]:
                print("   Period:", item.get("re_from_date"), "to", item.get("re_to_date"))
                print("   Format:", item.get("re_format"), "| Audited:", item.get("re_audited"))
                print("   Income:", item.get("re_total_income"), "| Sales:", item.get("re_net_sales"))
                print("   PBT:", item.get("re_pbt"), "| PAT:", item.get("re_pat"))
                print("   XBRL link:", item.get("re_xbrl_url"))
    except Exception as e:
        print(f"Error {sym}: {e}")
