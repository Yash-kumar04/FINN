"""
Download Results PDF from NSE and test BSE API endpoints
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import json
import requests
import fitz # PyMuPDF
from curl_cffi import requests as curl_requests

OUT_DIR = "pipeline/probe_output"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Download and extract DIXON results PDF from NSE
target_pdf_url = "https://nsearchives.nseindia.com/corporate/DIXON_30102026160547_Outcome30102026.pdf"
print(f"Downloading NSE Results Filing PDF: {target_pdf_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/pdf,application/xhtml+xml,text/html,*/*",
    "Referer": "https://www.nseindia.com/"
}

pdf_resp = requests.get(target_pdf_url, headers=headers, timeout=25)
print(f"PDF download HTTP status: {pdf_resp.status_code}, Length: {len(pdf_resp.content)} bytes")

extracted_lines = []
if pdf_resp.status_code == 200:
    doc = fitz.open(stream=pdf_resp.content, filetype="pdf")
    total_pages = len(doc)
    extracted_lines.append(f"Source URL: {target_pdf_url}")
    extracted_lines.append(f"Subject: Financial Results for period ended September 30, 2026 (Q2 FY27)")
    extracted_lines.append(f"Total Pages: {total_pages}")
    
    total_chars = 0
    pages_text = []
    for p_no in range(min(total_pages, 8)):
        p_text = doc[p_no].get_text()
        total_chars += len(p_text)
        pages_text.append(f"--- PAGE {p_no + 1} ---\n{p_text}")
        
    extracted_lines.append(f"Extracted Chars (First {min(total_pages, 8)} pages): {total_chars}")
    extracted_lines.append(f"\nFirst 500 characters:\n{doc[0].get_text()[:500]}")
    extracted_lines.append("\n" + "\n".join(pages_text))
    print(f"✅ Successfully extracted text from {total_pages} pages! Total characters sampled: {total_chars}")
else:
    extracted_lines.append(f"Failed to download PDF: HTTP {pdf_resp.status_code}")

with open(f"{OUT_DIR}/results_pdf_extracted.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(extracted_lines))
print(f"Saved to {OUT_DIR}/results_pdf_extracted.txt")

# 2. Probe BSE Corporate Announcements with different endpoints / headers
print("\n--- Probing BSE Corporate Announcements Fallback ---")
bse_tests = [
    {
        "name": "BSE API Announcements GetData",
        "url": "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?pageno=1&strCat=-1&strPrevDate=&strScrip=&strSearch=P&strToDate=&strType=C",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bseindia.com/corporates/ann.html",
            "Origin": "https://www.bseindia.com"
        }
    },
    {
        "name": "BSE API CorpAnn Scrip 540699 (DIXON)",
        "url": "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?pageno=1&strCat=-1&strPrevDate=&strScrip=540699&strSearch=P&strToDate=&strType=C",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bseindia.com/"
        }
    }
]

bse_results = {}
for test in bse_tests:
    try:
        # Try with curl_cffi chrome impersonation
        r = curl_requests.get(test["url"], headers=test["headers"], impersonate="chrome120", timeout=10)
        print(f"[{test['name']}] Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            table = data.get("Table", [])
            bse_results[test["name"]] = {
                "status": r.status_code,
                "count": len(table),
                "sample": table[0] if table else None
            }
            print(f"   Success! Received {len(table)} items from BSE.")
        else:
            bse_results[test["name"]] = {"status": r.status_code, "text": r.text[:200]}
    except Exception as e:
        bse_results[test["name"]] = {"error": str(e)}
        print(f"   Error: {e}")

# If api.bseindia.com blocks, test bseindia.com web scrape or RSS
try:
    rss_url = "https://www.bseindia.com/data/xml/corpann.xml"
    rss_resp = curl_requests.get(rss_url, impersonate="chrome120", timeout=8)
    bse_results["BSE_RSS"] = {"status": rss_resp.status_code, "length": len(rss_resp.content)}
    print(f"[BSE RSS] Status: {rss_resp.status_code}")
except Exception as e:
    bse_results["BSE_RSS"] = {"error": str(e)}

with open(f"{OUT_DIR}/bse_announcements_fallback.json", "w", encoding="utf-8") as f:
    json.dump(bse_results, f, indent=2)
print(f"Saved BSE fallback probe to {OUT_DIR}/bse_announcements_fallback.json")

