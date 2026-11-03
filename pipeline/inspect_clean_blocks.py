import fitz, sys
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except: pass

doc = fitz.open("pipeline/downloads/DIXON_Outcome30102026.pdf")
p11 = doc[10]
blocks = p11.get_text("blocks")

for b_idx in range(255, len(blocks)):
    b = blocks[b_idx]
    print(f"=== BLOCK {b_idx} ===")
    print(b[4])

