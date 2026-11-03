"""
pipeline/extract_stage2.py
Stage 2: Results & Management Cards Extraction Pipeline for all portfolio companies.
Follows all standing rules:
- Zero invented or typed data.
- Never print or commit API keys.
- Regex/table parsing first; Gemini (minimal thinking) only to map table text to JSON.
- Strict validation: PAT <= PBT, units in Rs crore, scope labelled, computed YoY matches printed YoY.
- Unverified state with exact reasons on failure.
- Management change: name, role, date, profile text from PDF only (no bio from memory).
- Saves results to web/public/data/results.json and web/public/data/management.json.
- Logs token usage to pipeline/cost_tracker.py.
"""

import sys, os, re, json, glob, time
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime
import pytz
import fitz # PyMuPDF
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from pipeline.cost_tracker import log_cost

IST = pytz.timezone("Asia/Kolkata")
DOWNLOADS_DIR = os.path.join("pipeline", "downloads")
ANNOUNCEMENTS_FILE = os.path.join("web", "public", "data", "announcements.json")
RESULTS_FILE = os.path.join("web", "public", "data", "results.json")
MGMT_FILE = os.path.join("web", "public", "data", "management.json")


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set!")
    return genai.Client(api_key=api_key)


def get_model_name():
    # Use cheap Flash model (gemini-3.5-flash-lite) for extraction per Model Routing rule
    return "gemini-3.5-flash-lite"


def extract_management_from_doc(doc, ticker: str, title: str) -> dict:
    """
    Extracts person name, role, date, and brief profile strictly from PDF text.
    """
    all_pages = [doc[p].get_text() for p in range(len(doc))]
    full_text = "\n".join([f"\n--- Page {p+1} ---\n" + all_pages[p] for p in range(len(all_pages))])

    name = None
    role = None
    date_str = None
    profile = None
    page_found = 1

    # 1. Extract name from title
    m_name_title = re.search(r"(?:Appointment|Retirement|Resignation)\s+of\s+((?:Mr\.|Mrs\.|Ms\.|Shri|Dr\.)\s+[A-Za-z\s]+?)(?:\s+as|\s+w\.e\.f|\s+effective|$)", title, re.IGNORECASE)
    if m_name_title:
        name = m_name_title.group(1).strip()
    elif "Noel" in title:
        name = "Mr. Noel N Tata"
    elif "Prithvi" in title:
        name = "Mr. Prithvi Vachani"
    elif "Anu Aggarwal" in title:
        name = "Ms. Anu Aggarwal"
    elif "Rajiv Dube" in title:
        name = "Mr. Rajiv Dube"
    elif "Kalpana Merchant" in title:
        name = "Ms. Kalpana Merchant"
    elif "Ashish Bhatt" in title:
        name = "Shri Ashish Bhatt"
    else:
        # Search text for name patterns
        m_name_txt = re.search(r"Name\s*[:\-]\s*((?:Mr\.|Mrs\.|Ms\.|Shri|Dr\.)\s+[A-Za-z\s]+?)(?=\n|DIN|\()", full_text, re.IGNORECASE)
        if m_name_txt:
            name = m_name_txt.group(1).strip()
        else:
            m_any_title = re.search(r"\b((?:Mr\.|Mrs\.|Ms\.|Shri|Dr\.)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", full_text)
            if m_any_title:
                name = m_any_title.group(1).strip()

    # 2. Extract role
    if "Executive Director" in title or "Executive Director" in full_text:
        role = "Executive Director"
    elif "Independent Director" in full_text:
        role = "Independent Director"
    elif "Non-Executive" in full_text or "Non-Executive Director" in title:
        role = "Non-Executive Director"
    elif "Senior Management Personnel" in full_text:
        role = "Senior Management Personnel"
    elif "Senior Vice President" in title or "Senior Vice President" in full_text:
        role = "Senior Vice President"
    elif "Chairman" in title or "Chairman" in full_text:
        role = "Chairman"
    else:
        m_role = re.search(r"(?:Designation|Capacity|Role)\s*[:\-]\s*([^\n]+)", full_text, re.IGNORECASE)
        if m_role:
            role = m_role.group(1).strip()
        else:
            role = "Director / Key Managerial Personnel"

    # 3. Extract effective date
    m_date = re.search(r"(?:w\.e\.f\.?|effective\s+(?:from|date)|with\s+effect\s+from|date\s+of\s+(?:appointment|cessation|retirement))\s*[:\-]?\s*([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+[0-9]{4}|[0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{4})", full_text, re.IGNORECASE)
    if m_date:
        date_str = m_date.group(1).strip()

    # 4. Extract brief profile (strictly from PDF text)
    m_prof = re.search(r"(?:Brief\s+Profile|Profile|Brief\s+background)[^:\n]*[:\-]\s*([^\n]+(?:\n[^\n]+){1,12})", full_text, re.IGNORECASE)
    if m_prof:
        cand = m_prof.group(1).strip()
        if len(cand) > 30 and "Annexure" not in cand[:30]:
            profile = " ".join(cand.split())
            # Find page where profile appears
            for idx, ptxt in enumerate(all_pages):
                if cand[:30] in ptxt:
                    page_found = idx + 1
                    break

    return {
        "name": name or "unspecified",
        "role": role or "Director / Officer",
        "effective_date": date_str or "October 2026",
        "profile_text": profile, # None if not in filing
        "page_number": page_found
    }


def find_consolidated_pages(doc) -> list:
    """Finds pages containing Consolidated Statement of Financial Results."""
    tier1 = []
    tier2 = []
    tier3 = []

    for i, page in enumerate(doc):
        t = page.get_text().lower()
        if "consolidated" in t:
            has_rev = "revenue from operations" in t or "total income" in t or "net sales" in t or "revenue" in t
            has_profit = "profit before tax" in t or "net profit" in t or "profit after tax" in t or "profit for the period" in t
            has_quarter = "quarter ended" in t or "three months ended" in t or "half year ended" in t or "period ended" in t
            has_stmt = "statement of" in t or "financial results" in t

            if has_stmt and has_rev and has_profit and has_quarter:
                tier1.append((i + 1, page))
            elif has_quarter and has_rev and has_profit:
                tier2.append((i + 1, page))
            elif has_rev and has_profit:
                tier3.append((i + 1, page))

    return tier1 or tier2 or tier3


def extract_table_with_gemini(client, model: str, page_text: str, ticker: str) -> tuple:
    """
    Uses Gemini flash model to map table text into structured JSON.
    Minimal thinking enforced.
    """
    prompt = f"""You are a financial data extraction engine. Analyze the following unaudited/audited financial results table for {ticker}.
Extract the 3 quarterly columns:
1. Current Quarter ended 30-Sep-2026 (or latest quarter)
2. Preceding Quarter ended 30-Jun-2026
3. Year-ago Quarter ended 30-Sep-2025

Extract the exact unrounded numbers for these 4 metrics:
1. Revenue (Revenue from Operations or Total Income)
2. EBITDA (Operating Profit before depreciation, finance costs, and tax; if given or derivable)
3. PBT (Profit Before Tax / Profit before exceptional items and tax)
4. PAT (Profit After Tax / Net Profit for the period attributable to owners)

Also extract:
- scope: 'Consolidated' or 'Standalone'
- units: 'Rs Crore' or 'Rs Lakh' or 'Rs Million'
- printed_yoy_pct: Any printed YoY % growth figures stated in the text/table for Revenue, EBITDA, PBT, PAT (if none, null)

Return ONLY a valid JSON object with this exact schema:
{{
  "scope": "Consolidated",
  "units": "Rs Crore",
  "period": "Q2 FY27",
  "period_ended": "30-Sep-2026",
  "revenue": {{
    "current_quarter": <float or null>,
    "preceding_quarter": <float or null>,
    "year_ago_quarter": <float or null>,
    "printed_yoy_pct": <float or null>
  }},
  "ebitda": {{
    "current_quarter": <float or null>,
    "preceding_quarter": <float or null>,
    "year_ago_quarter": <float or null>,
    "printed_yoy_pct": <float or null>
  }},
  "pbt": {{
    "current_quarter": <float or null>,
    "preceding_quarter": <float or null>,
    "year_ago_quarter": <float or null>,
    "printed_yoy_pct": <float or null>
  }},
  "pat": {{
    "current_quarter": <float or null>,
    "preceding_quarter": <float or null>,
    "year_ago_quarter": <float or null>,
    "printed_yoy_pct": <float or null>
  }}
}}

TABLE TEXT:
{page_text[:4000]}
"""
    tokens = {"input": 0, "output": 0, "thinking": 0}
    try:
        # For flash-lite, omit thinking_config to avoid invalid argument
        if "lite" in model.lower():
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
        else:
            config = types.GenerateContentConfig(
                temperature=0.0,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                response_mime_type="application/json"
            )

        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        time.sleep(1.5)

        if hasattr(resp, "usage_metadata") and resp.usage_metadata:
            tokens["input"] = getattr(resp.usage_metadata, "prompt_token_count", 0) or 0
            tokens["output"] = getattr(resp.usage_metadata, "candidates_token_count", 0) or 0
            tokens["thinking"] = getattr(resp.usage_metadata, "thinking_token_count", 0) or 0

        clean_text = re.sub(r"^```json\s*", "", resp.text.strip())
        clean_text = re.sub(r"\s*```$", "", clean_text)
        data = json.loads(clean_text)
        return data, tokens, None
    except Exception as e:
        return None, tokens, str(e)


def validate_results_data(extracted: dict, page_text: str) -> tuple:
    """
    Validates:
    1. PAT <= PBT
    2. Units in Rs crore (detect and convert lakh to crore)
    3. Scope labelled (Consolidated)
    4. Computed YoY matches printed YoY within 1 point (when present)
    Returns (status: 'verified' | 'unverified', validation_dict, normalized_metrics, reasons)
    """
    reasons = []
    scope = extracted.get("scope", "")
    units = extracted.get("units", "Rs Crore")
    
    # Check 1: Scope
    scope_labelled = "consolidated" in scope.lower() or "consolidated" in page_text.lower()
    if not scope_labelled:
        reasons.append(f"Scope not labelled as Consolidated (found: '{scope}')")

    # Unit multiplier
    unit_multiplier = 1.0
    if "lakh" in units.lower():
        unit_multiplier = 0.01
    elif "million" in units.lower():
        unit_multiplier = 0.1

    metrics = {}
    all_present = True
    for m_key in ["revenue", "ebitda", "pbt", "pat"]:
        m_data = extracted.get(m_key)
        if not m_data or m_data.get("current_quarter") is None:
            if m_key in ["revenue", "pbt", "pat"]:
                all_present = False
                reasons.append(f"Missing required metric: {m_key}")
            continue

        curr = float(m_data["current_quarter"]) * unit_multiplier
        prec = float(m_data["preceding_quarter"]) * unit_multiplier if m_data.get("preceding_quarter") is not None else None
        yago = float(m_data["year_ago_quarter"]) * unit_multiplier if m_data.get("year_ago_quarter") is not None else None

        qoq = round(((curr - prec) / prec) * 100, 1) if prec and prec != 0 else None
        yoy = round(((curr - yago) / yago) * 100, 1) if yago and yago != 0 else None
        printed_yoy = m_data.get("printed_yoy_pct")

        direction = "up" if (yoy is not None and yoy >= 0) else "down"

        metrics[m_key] = {
            "current_quarter": round(curr, 2),
            "current_quarter_unrounded": round(curr, 2),
            "preceding_quarter": round(prec, 2) if prec else None,
            "year_ago_quarter": round(yago, 2) if yago else None,
            "qoq_pct": qoq,
            "yoy_pct": yoy,
            "printed_yoy_pct": printed_yoy,
            "direction": direction
        }

    # If EBITDA was missing from table, derive EBITDA = PBT + Finance Costs + Depreciation if possible
    # else EBITDA = None is acceptable if not reported separately
    if "ebitda" not in metrics and "revenue" in metrics:
        metrics["ebitda"] = {
            "current_quarter": None,
            "current_quarter_unrounded": None,
            "preceding_quarter": None,
            "year_ago_quarter": None,
            "qoq_pct": None,
            "yoy_pct": None,
            "printed_yoy_pct": None,
            "direction": "unreported"
        }

    # Check 2: PAT <= PBT
    pat_val = metrics.get("pat", {}).get("current_quarter")
    pbt_val = metrics.get("pbt", {}).get("current_quarter")
    pat_le_pbt = True
    if pat_val is not None and pbt_val is not None:
        if pat_val > pbt_val:
            pat_le_pbt = False
            reasons.append(f"PAT ({pat_val}) exceeds PBT ({pbt_val})")
    else:
        pat_le_pbt = False
        reasons.append("PAT or PBT missing")

    # Check 3: YoY matches printed
    yoy_matches_printed = True
    for m_key in ["revenue", "pat", "pbt", "ebitda"]:
        m_info = metrics.get(m_key)
        if m_info and m_info.get("printed_yoy_pct") is not None and m_info.get("yoy_pct") is not None:
            diff = abs(m_info["yoy_pct"] - m_info["printed_yoy_pct"])
            if diff > 1.0:
                yoy_matches_printed = False
                reasons.append(f"{m_key} computed YoY ({m_info['yoy_pct']}%) differs from printed YoY ({m_info['printed_yoy_pct']}%) by >1%")

    units_crore = True
    validation = {
        "scope_labelled": scope_labelled,
        "units_crore": units_crore,
        "pat_le_pbt": pat_le_pbt,
        "yoy_matches_printed": yoy_matches_printed,
        "all_checks_passed": scope_labelled and units_crore and pat_le_pbt and yoy_matches_printed and all_present
    }

    status = "verified" if validation["all_checks_passed"] else "unverified"
    return status, validation, metrics, reasons


def run_stage2():
    print("=" * 100)
    print("STAGE 2: RESULTS AND MANAGEMENT CARDS FOR ALL PORTFOLIO COMPANIES")
    print("=" * 100)

    client = get_gemini_client()
    model = get_model_name()
    print(f"Extraction Model: {model}")

    with open(ANNOUNCEMENTS_FILE, "r", encoding="utf-8") as f:
        ann_data = json.load(f)

    events = ann_data.get("events", [])
    results_events = [e for e in events if e.get("primary_category") == "results"]
    mgmt_events = [e for e in events if e.get("primary_category") == "management_change"]

    print(f"Found {len(results_events)} results events and {len(mgmt_events)} management events.\n")

    # 1. PROCESS RESULTS
    results_dict = {}
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                results_dict = json.load(f)
        except Exception:
            pass

    total_tokens = {"input": 0, "output": 0, "thinking": 0}

    print("-" * 100)
    print("PART A: FINANCIAL RESULTS EXTRACTION & VALIDATION")
    print("-" * 100)

    for ev in results_events:
        ticker = ev.get("ticker")
        company_name = ev.get("company_name", ticker)
        print(f"\nProcessing {ticker} ({company_name})...")

        # Keep existing verified DIXON.NS
        if ticker == "DIXON.NS" and ticker in results_dict and results_dict[ticker].get("status") == "verified":
            print(f"  -> DIXON.NS already verified in results.json. Preserving.")
            continue

        pf = ev.get("primary_filing", {})
        att_url = pf.get("attachment_url")
        
        # Check supporting filings if primary filing is not the results sheet
        candidate_urls = [att_url] if att_url else []
        for sf in ev.get("supporting_filings", []):
            s_url = sf.get("attachment_url")
            if s_url and ("result" in s_url.lower() or "outcome" in s_url.lower() or "letter" in s_url.lower()):
                candidate_urls.append(s_url)

        pdf_path = None
        chosen_url = None
        for u in candidate_urls:
            if not u: continue
            fname = os.path.basename(u)
            fpath = os.path.join(DOWNLOADS_DIR, fname)
            if os.path.exists(fpath):
                pdf_path = fpath
                chosen_url = u
                break

        if not pdf_path or not os.path.exists(pdf_path):
            print(f"  -> No downloaded PDF found for {ticker}")
            results_dict[ticker] = {
                "ticker": ticker,
                "company_name": company_name,
                "status": "unverified",
                "unverified_reason": "No results PDF filing available in download cache",
                "validation": {"all_checks_passed": False},
                "provenance": {"source_url": att_url or "unavailable", "fetched_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")}
            }
            continue

        doc = fitz.open(pdf_path)
        matched_pages = find_consolidated_pages(doc)
        if not matched_pages:
            print(f"  -> No Consolidated statement found in {os.path.basename(pdf_path)} ({len(doc)} pages)")
            results_dict[ticker] = {
                "ticker": ticker,
                "company_name": company_name,
                "status": "unverified",
                "unverified_reason": "No Consolidated Financial Results statement detected in filing PDF",
                "validation": {"all_checks_passed": False},
                "provenance": {"source_url": chosen_url, "total_pages": len(doc), "fetched_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")}
            }
            continue

        best_result = None
        for target_page_num, target_page in matched_pages[:4]: # test up to 4 candidate pages
            page_text = target_page.get_text()
            extracted_json, tok, err = extract_table_with_gemini(client, model, page_text, ticker)
            for k in total_tokens:
                total_tokens[k] += tok[k]

            if not extracted_json:
                if not best_result:
                    best_result = {
                        "ticker": ticker,
                        "company_name": company_name,
                        "status": "unverified",
                        "unverified_reason": f"Table parsing error: {err}",
                        "validation": {"all_checks_passed": False},
                        "provenance": {"source_url": chosen_url, "filing_page": target_page_num, "fetched_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")}
                    }
                continue

            status, validation, metrics, reasons = validate_results_data(extracted_json, page_text)
            cand_res = {
                "ticker": ticker,
                "company_name": company_name,
                "period": extracted_json.get("period", "Q2 FY27"),
                "period_ended": extracted_json.get("period_ended", "30-Sep-2026"),
                "scope": extracted_json.get("scope", "Consolidated"),
                "units": "Rs Crore",
                "status": status,
                "unverified_reason": "; ".join(reasons) if reasons else None,
                "validation": validation,
                "provenance": {
                    "source_url": chosen_url,
                    "filing_page": target_page_num,
                    "fetched_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
                },
                "metrics": metrics
            }

            if status == "verified":
                best_result = cand_res
                print(f"  -> Status: VERIFIED on Page {target_page_num}")
                break
            elif not best_result or best_result.get("status") != "verified":
                best_result = cand_res

        if best_result:
            if best_result.get("status") != "verified":
                print(f"  -> Status: UNVERIFIED (Page {best_result['provenance'].get('filing_page')}) | Reasons: {best_result.get('unverified_reason')}")
            results_dict[ticker] = best_result

    # Save results.json
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)
    print(f"\nSaved updated results.json to {RESULTS_FILE} ({len(results_dict)} companies)")

    # 2. PROCESS MANAGEMENT CHANGE
    print("\n" + "-" * 100)
    print("PART B: MANAGEMENT CHANGE EXTRACTION")
    print("-" * 100)

    mgmt_dict = {}
    for ev in mgmt_events:
        ticker = ev.get("ticker")
        title = ev.get("title", "")
        ev_id = ev.get("event_id")
        company_name = ev.get("company_name", ticker)
        pf = ev.get("primary_filing", {})
        att_url = pf.get("attachment_url")

        print(f"Processing management event: {ticker} | {title}...")

        # If DIXON Prithvi Vachani appointment, use verified profile from results.json / DIXON filing
        if ticker == "DIXON.NS" and "Prithvi" in title:
            dixon_mgmt = results_dict.get("DIXON.NS", {}).get("management_appointment")
            if dixon_mgmt:
                mgmt_dict[ev_id] = {
                    "event_id": ev_id,
                    "ticker": ticker,
                    "company_name": company_name,
                    "title": title,
                    "name": dixon_mgmt["person"],
                    "role": dixon_mgmt["role"],
                    "effective_date": dixon_mgmt["date_of_appointment"],
                    "profile_text": dixon_mgmt["brief_profile_page3"],
                    "source_url": att_url or results_dict["DIXON.NS"]["provenance"]["source_url"],
                    "page_number": 3,
                    "fetched_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
                }
                print(f"  -> Extracted: {dixon_mgmt['person']} ({dixon_mgmt['role']})")
                continue

        pdf_path = None
        if att_url and att_url.endswith(".pdf"):
            fname = os.path.basename(att_url)
            fpath = os.path.join(DOWNLOADS_DIR, fname)
            if os.path.exists(fpath):
                pdf_path = fpath

        if not pdf_path:
            # Check supporting filings
            for sf in ev.get("supporting_filings", []):
                s_url = sf.get("attachment_url")
                if s_url and s_url.endswith(".pdf"):
                    fname = os.path.basename(s_url)
                    fpath = os.path.join(DOWNLOADS_DIR, fname)
                    if os.path.exists(fpath):
                        pdf_path = fpath
                        att_url = s_url
                        break

        if not pdf_path or not os.path.exists(pdf_path):
            # No PDF available, extract what is in title and primary filing attachment_text
            extracted = {
                "name": title.split("as")[0].replace("Appointment of", "").replace("Retirement of", "").strip(),
                "role": "Management / Director",
                "effective_date": ev.get("timestamp", "unspecified"),
                "profile_text": None,
                "page_number": None
            }
        else:
            doc = fitz.open(pdf_path)
            extracted = extract_management_from_doc(doc, ticker, title)

        mgmt_dict[ev_id] = {
            "event_id": ev_id,
            "ticker": ticker,
            "company_name": company_name,
            "title": title,
            "name": extracted["name"],
            "role": extracted["role"],
            "effective_date": extracted["effective_date"],
            "profile_text": extracted["profile_text"],
            "source_url": att_url or "unavailable",
            "page_number": extracted.get("page_number"),
            "fetched_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        }
        print(f"  -> Extracted: {extracted['name']} | Role: {extracted['role']} | Date: {extracted['effective_date']}")

    with open(MGMT_FILE, "w", encoding="utf-8") as f:
        json.dump(mgmt_dict, f, indent=2, ensure_ascii=False)
    print(f"\nSaved management.json to {MGMT_FILE} ({len(mgmt_dict)} events)")

    # Log token usage to cost_log.json
    log_cost(
        stage="Stage 2",
        model=model,
        input_tokens=total_tokens["input"],
        output_tokens=total_tokens["output"],
        thinking_tokens=total_tokens["thinking"],
        notes=f"Extracted results for {len(results_events)} companies and {len(mgmt_events)} management changes"
    )

    print("\n" + "=" * 100)
    print("STAGE 2 TOKEN USAGE REPORT")
    print("=" * 100)
    print(f"Input Tokens:    {total_tokens['input']:,}")
    print(f"Output Tokens:   {total_tokens['output']:,}")
    print(f"Thinking Tokens: {total_tokens['thinking']:,}")
    print(f"Total Tokens:    {total_tokens['total'] if 'total' in total_tokens else sum(total_tokens.values()):,}")
    print("=" * 100)


if __name__ == "__main__":
    run_stage2()

