import fitz
import re
import json
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

pdf_path = "pipeline/downloads/DIXON_Outcome30102026.pdf"
doc = fitz.open(pdf_path)

# 1. Page 1 Text (Highlights & Appointment Intimation)
p1_text = doc[0].get_text()

# 2. Page 3 Text (Annexure A - Prithvi Vachani Details)
p3_text = doc[2].get_text()

# 3. Page 11 Text (Statement of Consolidated Financial Results)
p11_text = doc[10].get_text()

print("--- PAGE 1 HIGHLIGHTS PARSING ---")
# Extract key highlights table on Page 1
# Revenue from Operations (including other income) 21,863 | 42% ^
# EBIDTA 666 | 37% v
# PBT 532 | 42% v
# PAT 411 | 45% v
p1_clean = re.sub(r'\s+', ' ', p1_text)
print("Page 1 snippet:", p1_clean[p1_clean.find("Following are the key highlights"):p1_clean.find("The detailed format")])

# Extract Prithvi Vachani from Page 1
p1_mgmt_match = re.search(r"Appointment of Mr\. Prithvi Vachani.*?(?=\n\s*\n\s*\n|Regd\. Office)", p1_text, re.DOTALL)
if p1_mgmt_match:
    print("\nPage 1 Mgmt Excerpt:\n", p1_mgmt_match.group(0).strip())

# Extract Prithvi Vachani from Page 3 Annexure A
print("\n--- PAGE 3 ANNEXURE A PARSING ---")
for line in p3_text.split("\n"):
    if any(k in line.lower() for k in ["name of director", "appointment", "date of appointment", "term of appointment", "prithvi vachani"]):
        print(" ", line.strip())

# Extract table lines on Page 11
print("\n--- PAGE 11 CONSOLIDATED TABLE PARSING ---")
# Find header and columns
lines = [l.strip() for l in p11_text.split("\n") if l.strip()]
for idx, l in enumerate(lines[:40]):
    print(f"{idx}: {l}")

