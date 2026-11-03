import json
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")
def parse_ts(ts_str):
    return datetime.strptime(ts_str, "%d-%b-%Y %H:%M:%S").replace(tzinfo=IST)

ann = json.load(open('web/public/data/announcements.json', encoding='utf-8'))
for sym in ['RELIANCE.NS', 'DIXON.NS']:
    anns = ann['tickers'][sym]['announcements']
    print(f"=== {sym} announcements ({len(anns)}) ===")
    for a in anns:
        desc = a.get('desc')
        ts = a.get('timestamp')
        cat = a.get('classification', {}).get('category')
        tags = a.get('classification', {}).get('secondary_tags', [])
        print(f"  {ts} | cat={cat} | tags={tags} | {desc[:60]}")

