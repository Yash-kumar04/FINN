import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import fitz

doc = fitz.open("pipeline/downloads/ICICI2022_17102026152608_NSEBSE17102026.pdf")
p13 = doc[12].get_text()
lines = [l.strip() for l in p13.split("\n") if l.strip()]

for i in range(80, 225):
    print(f"{i:3d}: {lines[i]}")
