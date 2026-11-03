import sys, json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Find the raw filing for DIXON management change in the feed
with open("web/public/data/announcements.json", encoding="utf-8") as f:
    ann = json.load(f)

print("=== DIXON.NS raw management filings in feed ===")
for rec in ann.get("feed", []):
    if rec.get("ticker") == "DIXON.NS" and rec["classification"]["category"] == "management_change":
        print(f"  seq_id: {rec.get('seq_id')}")
        print(f"  desc: {rec.get('desc')}")
        print(f"  attachment_text (full): {rec.get('attachment_text')}")
        print(f"  timestamp: {rec.get('timestamp')}")
        print()

print("=== ALL raw management filings in DIXON.NS announcements ===")
dixon_anns = ann.get("tickers", {}).get("DIXON.NS", {}).get("announcements", [])
for a in dixon_anns:
    print(f"  seq_id={a.get('seq_id')} | desc={a.get('desc')}")
    print(f"  text: {(a.get('attachment_text') or '')[:300]}")
    print()

print("=== ALL tickers with raw management announcements — full attachment text ===")
for sym, t in ann.get("tickers", {}).items():
    for a in t.get("announcements", []):
        desc = a.get("desc", "")
        text = a.get("attachment_text", "") or ""
        combined = (desc + " " + text).lower()
        if any(k in combined for k in ["change in director", "change in management", "appointment", "resignation", "retirement", "cessation"]):
            if any(k in combined for k in ["director", "kmp", "ceo", "cfo", "chairman", "president"]):
                print(f"{sym} | seq={a.get('seq_id')} | desc={desc}")
                print(f"  text: {text[:300]}")
                print()

