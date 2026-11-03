import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pipeline.research import fetch_screener_transcript_links

for ticker in ['KAYNES', 'M&M', 'ASTRAL', 'INFY']:
    try:
        links = fetch_screener_transcript_links(ticker, limit=5)
        print(f"{ticker}: Found {len(links)} transcripts")
        for l in links[:2]:
            print(f"   {l['screener_period']}: {l['url']}")
    except Exception as e:
        print(f"{ticker}: Failed - {e}")

