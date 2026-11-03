import fitz # PyMuPDF
import sys

doc = fitz.open("pipeline/downloads/DIXON_Outcome30102026.pdf")
print(f"Total pages: {len(doc)}")

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    first_line = text.strip().split("\n")[0] if text.strip() else "(empty)"
    has_consolidated = "consolidated" in text.lower()
    has_prithvi = "prithvi" in text.lower()
    has_vachani = "vachani" in text.lower()
    has_results = "revenue" in text.lower() or "profit" in text.lower()
    print(f"Page {page_num + 1}: len={len(text)} | first_line={first_line[:50]} | consol={has_consolidated} | results={has_results} | prithvi={has_prithvi} | vachani={has_vachani}")

