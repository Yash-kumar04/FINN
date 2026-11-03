import fitz, sys
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except: pass

doc = fitz.open("pipeline/downloads/DIXON_Outcome30102026.pdf")
p11 = doc[10]

# Let's inspect text blocks with their coordinates: page.get_text("blocks")
blocks = p11.get_text("blocks")
print(f"Total blocks on Page 11: {len(blocks)}")
for i, b in enumerate(blocks):
    # b is (x0, y0, x1, y1, text, block_no, block_type)
    text = b[4].strip().replace('\n', ' // ')
    if any(k in text.lower() for k in ["revenue", "profit", "tax", "income", "expenses", "ebitda", "ebidta", "30-sep-26", "particulars"]):
        print(f"Block {i} (y={b[1]:.1f}): {text[:120]}")

