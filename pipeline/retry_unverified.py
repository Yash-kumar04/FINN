import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import requests
import fitz

def check_pdf(url):
    fname = os.path.basename(url)
    path = os.path.join("pipeline", "downloads", fname)
    if not os.path.exists(path):
        print(f"Downloading {fname} from {url}...")
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(path, "wb") as f:
                    f.write(r.content)
            else:
                print(f"  Failed HTTP {r.status_code}")
                return None
        except Exception as e:
            print(f"  Download error: {e}")
            return None
    
    doc = fitz.open(path)
    total_pages = len(doc)
    text_len = sum(len(p.get_text()) for p in doc)
    print(f"PDF: {fname} | Pages: {total_pages} | Chars: {text_len}")
    return doc

print("--- 1. MARUTI ---")
doc_m = check_pdf("https://nsearchives.nseindia.com/corporate/MARUTI_27102026152412_QuickResults_27Oct2026_signed.pdf")
doc_m_pr = check_pdf("https://nsearchives.nseindia.com/corporate/MARUTI_27102026153704_STxIntimation_PR_27Oct2026.pdf")

print("\n--- 2. BAJAJ AUTO ---")
doc_b = check_pdf("https://nsearchives.nseindia.com/corporate/lkwalimbe_bajajauto_co_in_27102026152127_Q2Fy27Results.pdf")

print("\n--- 3. TRENT ---")
doc_t = check_pdf("https://nsearchives.nseindia.com/corporate/TRENT_29102026160446_DraftOutcomeofBM.pdf")
doc_t_pr = check_pdf("https://nsearchives.nseindia.com/corporate/TRENT_29102026162053_PressReleaseOct2026.pdf")

