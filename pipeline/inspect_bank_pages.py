import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import fitz

def dump_page(filename, page_num):
    doc = fitz.open(f"pipeline/downloads/{filename}")
    txt = doc[page_num - 1].get_text()
    print(f"=== {filename} Page {page_num} ===")
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        print(f"{i:3d}: {l}")

print("ICICIBANK:")
dump_page("ICICI2022_17102026152608_NSEBSE17102026.pdf", 13)

print("\nKOTAKBANK:")
dump_page("KMBLTAB_24102026131109_OutcomeofBMOct242026SIGNED.pdf", 7)
