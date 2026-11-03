import fitz
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

doc = fitz.open("pipeline/downloads/DIXON_Outcome30102026.pdf")
p11 = doc[10]

tabs = p11.find_tables()
tables_list = tabs.tables
print(f"Tables found on Page 11: {len(tables_list)}")
for i, tab in enumerate(tables_list):
    df = tab.extract()
    print(f"\nTable {i} ({len(df)} rows, {len(df[0]) if df else 0} cols):")
    for r in df[:20]:
        print(" | ".join(str(c).replace('\n', ' ') for c in r if c is not None))
