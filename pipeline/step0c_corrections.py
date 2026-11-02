"""
Step 0c: Targeted corrections probes
1. Verify transcript counts on Screener for KAYNES and M&M (need >= 4 recent)
2. Parse the 3-column results table from DIXON filing PDF for QoQ data
3. Test NSE XBRL structured results endpoint
4. Gemini: test thinking budget control, log reasoning tokens separately, read model from env
5. Confirm TRENT has zero transcripts (document the gap)
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
import time
import requests
import fitz
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

OUT_DIR = "pipeline/probe_output"
os.makedirs(OUT_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# =========================================================================
# PROBE 1: Transcript counts on Screener for research ticker candidates
# =========================================================================
print("=" * 80)
print("PROBE 1: SCREENER TRANSCRIPT COUNTS FOR RESEARCH TICKER CANDIDATES")
print("=" * 80)

def count_screener_transcripts(ticker_code):
    """Return list of transcript links with titles from Screener."""
    url = f"https://www.screener.in/company/{ticker_code}/consolidated/"
    r = requests.get(url, headers=headers, timeout=12)
    if r.status_code != 200:
        url = f"https://www.screener.in/company/{ticker_code}/"
        r = requests.get(url, headers=headers, timeout=12)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "transcripts": []}

    soup = BeautifulSoup(r.text, "html.parser")
    transcripts = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if "transcript" in text.lower() or "concall" in text.lower():
            full_url = href if href.startswith("http") else "https://www.screener.in" + href
            transcripts.append({"text": text, "url": full_url})
    return {"count": len(transcripts), "transcripts": transcripts}

candidates = ["KAYNES", "M&M", "TRENT", "DIXON", "ASTRAL"]
transcript_report = {}

for ticker in candidates:
    print(f"\n--- {ticker} ---")
    result = count_screener_transcripts(ticker)
    transcript_report[ticker] = result
    if "error" in result:
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  Total transcript links: {result['count']}")
        # Show first 6 titles to confirm recency
        for i, t in enumerate(result["transcripts"][:6]):
            print(f"  [{i+1}] {t['text']}")
            print(f"      -> {t['url'][:80]}...")

with open(f"{OUT_DIR}/screener_transcript_counts.json", "w", encoding="utf-8") as f:
    json.dump(transcript_report, f, indent=2)
print(f"\nSaved to {OUT_DIR}/screener_transcript_counts.json")


# =========================================================================
# PROBE 2: Parse the 3-column results table from DIXON Q2 filing PDF
# =========================================================================
print("\n" + "=" * 80)
print("PROBE 2: PARSE 3-COLUMN RESULTS TABLE FROM DIXON Q2 FILING PDF")
print("=" * 80)

# Re-download and extract the full tabular data
pdf_url = "https://nsearchives.nseindia.com/corporate/DIXON_30102026160547_Outcome30102026.pdf"
pdf_resp = requests.get(pdf_url, headers=headers, timeout=20)

if pdf_resp.status_code == 200:
    doc = fitz.open(stream=pdf_resp.content, filetype="pdf")
    
    # Extract tables from each page
    tables_output = []
    tables_output.append(f"PDF URL: {pdf_url}")
    tables_output.append(f"Total Pages: {len(doc)}")
    tables_output.append("")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Try extracting tables using PyMuPDF's find_tables
        try:
            tabs = page.find_tables()
            if tabs and len(tabs.tables) > 0:
                tables_output.append(f"=== PAGE {page_num + 1}: Found {len(tabs.tables)} table(s) ===")
                for t_idx, table in enumerate(tabs.tables):
                    tables_output.append(f"  Table {t_idx + 1}: {table.row_count} rows x {table.col_count} cols")
                    extracted = table.extract()
                    for row_idx, row in enumerate(extracted):
                        tables_output.append(f"    Row {row_idx}: {row}")
                tables_output.append("")
        except Exception as e:
            tables_output.append(f"=== PAGE {page_num + 1}: table extraction error: {e} ===")
    
    # Also dump raw text of pages 2-5 where the actual SEBI format results table lives
    tables_output.append("\n" + "=" * 60)
    tables_output.append("RAW TEXT OF PAGES 2-6 (where SEBI format results live)")
    tables_output.append("=" * 60)
    for p in range(1, min(6, len(doc))):
        tables_output.append(f"\n--- RAW PAGE {p+1} ---")
        tables_output.append(doc[p].get_text())
    
    with open(f"{OUT_DIR}/dixon_results_tables.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(tables_output))
    print(f"Saved table extraction to {OUT_DIR}/dixon_results_tables.txt")
    
    # Print summary of what we found
    print("Table locations found:")
    for line in tables_output:
        if "Found" in line or "Table " in line:
            print(f"  {line.strip()}")
else:
    print(f"PDF download failed: HTTP {pdf_resp.status_code}")


# =========================================================================
# PROBE 3: TEST NSE XBRL STRUCTURED RESULTS ENDPOINT
# =========================================================================
print("\n" + "=" * 80)
print("PROBE 3: NSE XBRL / STRUCTURED RESULTS ENDPOINTS")
print("=" * 80)

nse_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results"
}

nse_session = requests.Session()
nse_session.headers.update(nse_headers)

# Prime cookies
try:
    nse_session.get("https://www.nseindia.com", timeout=10)
    time.sleep(1)
except Exception as e:
    print(f"NSE homepage cookie prime: {e}")

xbrl_tests = {}

# Test 1: NSE Financial Results API endpoint
# This returns structured quarterly results
try:
    # Latest results for a specific symbol
    fr_url = "https://www.nseindia.com/api/corporates-financial-results?index=equities&period=Quarterly"
    fr_resp = nse_session.get(fr_url, timeout=10)
    print(f"[NSE Financial Results API] Status: {fr_resp.status_code}")
    if fr_resp.status_code == 200:
        fr_data = fr_resp.json()
        xbrl_tests["financial_results_api"] = {
            "status": fr_resp.status_code,
            "count": len(fr_data) if isinstance(fr_data, list) else "not a list",
            "sample": fr_data[:2] if isinstance(fr_data, list) else str(fr_data)[:500]
        }
        if isinstance(fr_data, list) and len(fr_data) > 0:
            print(f"  Received {len(fr_data)} results entries")
            print(f"  Sample fields: {list(fr_data[0].keys()) if isinstance(fr_data[0], dict) else 'not dict'}")
            # Search for DIXON
            dixon_results = [x for x in fr_data if isinstance(x, dict) and x.get("symbol") == "DIXON"]
            if dixon_results:
                print(f"  Found DIXON result(s): {len(dixon_results)}")
                xbrl_tests["dixon_result"] = dixon_results[0]
    else:
        xbrl_tests["financial_results_api"] = {"status": fr_resp.status_code}
except Exception as e:
    xbrl_tests["financial_results_api"] = {"error": str(e)}
    print(f"  Error: {e}")

# Test 2: XBRL download endpoint  
try:
    # Check if XBRL data is available for the DIXON filing
    # NSE stores XBRL at nsearchives with specific naming
    xbrl_url = "https://www.nseindia.com/api/corporates-financial-results-data?index=equities&params=quarterly"
    xbrl_resp = nse_session.get(xbrl_url, timeout=10)
    print(f"[NSE XBRL Data Endpoint] Status: {xbrl_resp.status_code}")
    if xbrl_resp.status_code == 200:
        xbrl_data = xbrl_resp.json()
        xbrl_tests["xbrl_data_endpoint"] = {
            "status": xbrl_resp.status_code,
            "type": type(xbrl_data).__name__,
            "sample": str(xbrl_data)[:800]
        }
except Exception as e:
    xbrl_tests["xbrl_data_endpoint"] = {"error": str(e)}
    print(f"  Error: {e}")

# Test 3: Try the specific symbol financial results endpoint
try:
    sym_url = "https://www.nseindia.com/api/corporates-financial-results?index=equities&symbol=DIXON&period=Quarterly"
    sym_resp = nse_session.get(sym_url, timeout=10)
    print(f"[NSE DIXON Quarterly Results] Status: {sym_resp.status_code}")
    if sym_resp.status_code == 200:
        sym_data = sym_resp.json()
        xbrl_tests["dixon_quarterly"] = {
            "status": sym_resp.status_code,
            "type": type(sym_data).__name__,
            "sample": json.dumps(sym_data[:2] if isinstance(sym_data, list) else sym_data, indent=2)[:1000]
        }
        if isinstance(sym_data, list):
            print(f"  Found {len(sym_data)} quarterly result entries for DIXON")
            if len(sym_data) > 0 and isinstance(sym_data[0], dict):
                print(f"  Fields: {list(sym_data[0].keys())}")
    else:
        xbrl_tests["dixon_quarterly"] = {"status": sym_resp.status_code}
except Exception as e:
    xbrl_tests["dixon_quarterly"] = {"error": str(e)}
    print(f"  Error: {e}")

with open(f"{OUT_DIR}/nse_xbrl_tests.json", "w", encoding="utf-8") as f:
    json.dump(xbrl_tests, f, indent=2, default=str)
print(f"Saved XBRL test results to {OUT_DIR}/nse_xbrl_tests.json")


# =========================================================================
# PROBE 4: GEMINI THINKING TOKEN CONTROL & ENV-BASED MODEL SELECTION
# =========================================================================
print("\n" + "=" * 80)
print("PROBE 4: GEMINI THINKING BUDGET & TOKEN LOGGING")
print("=" * 80)

from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
# Read model from env, with fallback
model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
print(f"Model from env (GEMINI_MODEL): {model_name}")

client = genai.Client(api_key=api_key)

# First: verify the model is actually callable (not just listed)
print(f"\nVerifying model '{model_name}' is callable...")
try:
    verify_resp = client.models.generate_content(
        model=model_name,
        contents="Reply with exactly: MODEL_OK",
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            max_output_tokens=20
        )
    )
    print(f"  Model verification: {verify_resp.text.strip()}")
except Exception as e:
    print(f"  Model '{model_name}' FAILED verification: {e}")
    # Try fallback
    model_name = "gemini-3.5-flash"
    print(f"  Trying fallback model: {model_name}")

# Test 1: Minimal thinking budget (bulk extraction mode)
print(f"\nTest 1: Minimal thinking (thinking_budget=0) for bulk extraction")
test_prompt = """Extract the following from this text and return JSON:
{"revenue_cr": number, "ebitda_cr": number, "pbt_cr": number, "pat_cr": number, "period": string}

Text: Revenue from Operations 21,863 Cr (42% Up YoY), EBIDTA 666 Cr, PBT 532 Cr, PAT 411 Cr for Q2 FY27."""

t1_start = time.time()
resp1 = client.models.generate_content(
    model=model_name,
    contents=test_prompt,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        max_output_tokens=200
    )
)
t1_dur = time.time() - t1_start

usage1 = resp1.usage_metadata
t1_data = {
    "test": "minimal_thinking_budget_0",
    "model": model_name,
    "prompt_tokens": getattr(usage1, "prompt_token_count", None),
    "candidates_tokens": getattr(usage1, "candidates_token_count", None),
    "total_tokens": getattr(usage1, "total_token_count", None),
    "thinking_tokens": None,
    "latency_seconds": round(t1_dur, 2),
    "response": resp1.text.strip()
}

# Calculate thinking tokens: total - prompt - candidates
if all(v is not None for v in [t1_data["total_tokens"], t1_data["prompt_tokens"], t1_data["candidates_tokens"]]):
    t1_data["thinking_tokens"] = t1_data["total_tokens"] - t1_data["prompt_tokens"] - t1_data["candidates_tokens"]

print(f"  Input tokens:    {t1_data['prompt_tokens']}")
print(f"  Output tokens:   {t1_data['candidates_tokens']}")
print(f"  Thinking tokens: {t1_data['thinking_tokens']}")
print(f"  Total tokens:    {t1_data['total_tokens']}")
print(f"  Latency:         {t1_data['latency_seconds']}s")
print(f"  Response:        {t1_data['response'][:200]}")

# Test 2: Default thinking (for comparison)
print(f"\nTest 2: Default thinking (no budget set) for comparison")
t2_start = time.time()
resp2 = client.models.generate_content(
    model=model_name,
    contents=test_prompt,
    config=types.GenerateContentConfig(
        max_output_tokens=200
    )
)
t2_dur = time.time() - t2_start

usage2 = resp2.usage_metadata
t2_data = {
    "test": "default_thinking",
    "model": model_name,
    "prompt_tokens": getattr(usage2, "prompt_token_count", None),
    "candidates_tokens": getattr(usage2, "candidates_token_count", None),
    "total_tokens": getattr(usage2, "total_token_count", None),
    "thinking_tokens": None,
    "latency_seconds": round(t2_dur, 2),
    "response": resp2.text.strip()
}

if all(v is not None for v in [t2_data["total_tokens"], t2_data["prompt_tokens"], t2_data["candidates_tokens"]]):
    t2_data["thinking_tokens"] = t2_data["total_tokens"] - t2_data["prompt_tokens"] - t2_data["candidates_tokens"]

print(f"  Input tokens:    {t2_data['prompt_tokens']}")
print(f"  Output tokens:   {t2_data['candidates_tokens']}")
print(f"  Thinking tokens: {t2_data['thinking_tokens']}")
print(f"  Total tokens:    {t2_data['total_tokens']}")
print(f"  Latency:         {t2_data['latency_seconds']}s")
print(f"  Response:        {t2_data['response'][:200]}")

# Save both tests
gemini_cost_report = {
    "model_source": "env var GEMINI_MODEL or default",
    "model_used": model_name,
    "note_on_thinking_tokens": "total_tokens - prompt_tokens - candidates_tokens = hidden reasoning tokens billed as output",
    "note_on_models_list": "gemini-2.5-flash appears in models.list() but returns 404 on generate_content. Always verify with a real call.",
    "test_minimal_thinking": t1_data,
    "test_default_thinking": t2_data,
    "cost_saving": {
        "thinking_tokens_saved": (t2_data["thinking_tokens"] or 0) - (t1_data["thinking_tokens"] or 0),
        "recommendation": "Use thinking_budget=0 for structured extraction (classification, table parsing). Use default/higher budget only for promised-vs-delivered and bull/bear synthesis."
    }
}

with open(f"{OUT_DIR}/gemini_thinking_cost_report.json", "w", encoding="utf-8") as f:
    json.dump(gemini_cost_report, f, indent=2)
print(f"\nSaved thinking cost report to {OUT_DIR}/gemini_thinking_cost_report.json")


# =========================================================================
# PROBE 5: CORRECTION LOG — NO INVENTED CAUSES
# =========================================================================
print("\n" + "=" * 80)
print("PROBE 5: CORRECTION LOG")
print("=" * 80)

corrections = {
    "corrections_applied": [
        {
            "issue": "Agent wrote 'Dixon +12% followed its results'. This is a causal claim — a guess.",
            "context": "Dixon PAT was DOWN 45% YoY. Claiming the price rose 'because of results' is editorializing.",
            "fix": "Show price reaction (delta %, volume spike) next to results numbers without ever claiming causation.",
            "rule": "NEVER write 'rose because', 'fell due to', or any causal language linking price moves to events."
        },
        {
            "issue": "TRENT has 0 concall transcripts on Screener.",
            "context": "Promised-vs-Delivered requires multiple quarters of management commentary from earnings calls.",
            "fix": "Keep TRENT in portfolio (for Briefing tab), remove from research universe. Research tickers must have >= 4 recent transcript links on Screener."
        },
        {
            "issue": "gemini-2.5-flash appeared in models.list() but was not callable (404).",
            "fix": "Read model name from GEMINI_MODEL env var. Always make a verification generate call at pipeline startup before running extraction. Never trust models.list() alone."
        },
        {
            "issue": "Total tokens included 292 hidden reasoning tokens not logged separately.",
            "fix": "Log prompt_tokens, candidates_tokens, thinking_tokens (= total - prompt - candidates) separately per call. Use thinking_budget=0 for bulk extraction to minimize cost."
        },
        {
            "issue": "QoQ calculation impossible from headline filing text (only shows YoY).",
            "fix": "Parse the full 3-column SEBI-format results table from the PDF (current Q, preceding Q, year-ago Q). Also test NSE XBRL structured results as a cheaper/more accurate alternative to LLM extraction."
        },
        {
            "issue": "Cloud servers blocked by NSE/BSE/Screener.",
            "fix": "Run pipeline locally, commit snapshots to repo. On Render: serve pre-cached demo tickers from disk, fail live lookups with clear 'Data unavailable from cloud — run pipeline locally' message. Handle Render free-tier cold start (~60s) in the frontend with a loading state."
        }
    ]
}

with open(f"{OUT_DIR}/corrections_log.json", "w", encoding="utf-8") as f:
    json.dump(corrections, f, indent=2)
print("All corrections logged.")
print(json.dumps(corrections["corrections_applied"][0], indent=2))

print("\n" + "=" * 80)
print("STEP 0c COMPLETE")
print("=" * 80)

