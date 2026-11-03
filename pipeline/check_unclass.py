import json

with open('web/public/data/announcements.json', encoding='utf-8') as f:
    a = json.load(f)

unclass = [r for r in a.get('feed', []) if r['classification']['category'] == 'unclassified']
for r in unclass:
    d = r.get('desc', '')
    if any(k in d for k in ['Bagging', 'Insolvency', 'Action', 'Retirement', 'Appointment', 'Sale', 'Allotment']):
        txt = (r.get('attachment_text') or '').replace('\n', ' ')[:90]
        print(f"{r['ticker']:<15} | {d:<35} | {txt}")

