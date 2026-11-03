import sys, json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

with open("web/public/data/announcements.json", encoding="utf-8") as f:
    ann = json.load(f)

# =========================================================================
# ITEM 3: Management events — are they per person or per window?
# =========================================================================
print("=" * 80)
print("ITEM 3: MANAGEMENT CHANGE EVENTS — RAW DESC + PERSON NAMED")
print("=" * 80)

mgmt_events = [e for e in ann["events"] if e.get("primary_category") == "management_change"]
print(f"Total management_change events: {len(mgmt_events)}\n")

for i, ev in enumerate(mgmt_events, 1):
    print(f"[{i}] event_id: {ev['event_id']}")
    print(f"    ticker: {ev['ticker']}")
    print(f"    title:  {ev['title']}")
    print(f"    filing_count: {ev['filing_count']}")
    print(f"    timestamp: {ev['timestamp']}")
    pf = ev.get("primary_filing", {})
    print(f"    primary_filing desc:    {pf.get('desc')}")
    print(f"    primary_filing atttext: {(pf.get('attachment_text') or '')[:200]}")
    for j, sf in enumerate(ev.get("supporting_filings", []), 1):
        print(f"    supporting_filing[{j}] desc:    {sf.get('desc')}")
        print(f"    supporting_filing[{j}] atttext: {(sf.get('attachment_text') or '')[:200]}")
    print()

# Find DIXON management events specifically
print("\n--- DIXON management events (checking for Prithvi Vachani) ---")
dixon_mgmt = [e for e in ann["events"] if e.get("ticker") == "DIXON.NS" and e.get("primary_category") == "management_change"]
if not dixon_mgmt:
    print("NO management_change events for DIXON.NS")
else:
    for ev in dixon_mgmt:
        print(f"  event_id: {ev['event_id']}")
        pf = ev.get("primary_filing", {})
        print(f"  desc: {pf.get('desc')}")
        print(f"  text: {(pf.get('attachment_text') or '')[:300]}")

