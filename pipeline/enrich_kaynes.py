import sys, os, re, json, hashlib
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime
import pytz
import fitz
import requests
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from pipeline.cost_tracker import log_cost

IST = pytz.timezone("Asia/Kolkata")
AR_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/7b3ec474-8dc9-46bc-bf3b-64d55d3b6c30.pdf"
CACHE_DIR = os.path.join("pipeline", "cache", "transcripts")
KAYNES_JSON_PATH = os.path.join("web", "public", "data", "research", "KAYNES.json")

def verify_fact_on_page(doc, page_num: int, val_str: str) -> bool:
    if not (1 <= page_num <= len(doc)):
        return False
    txt = doc[page_num - 1].get_text()
    clean_val = val_str.replace("₹", "").replace(",", "").strip()
    clean_txt = txt.replace("₹", "").replace("`", "").replace(",", "")
    return (val_str in txt) or (clean_val in clean_txt) or (val_str.lower() in txt.lower())

def run():
    print("=" * 80)
    print("ENRICHING KAYNES RESEARCH DOSSIER WITH AUDITED ANNUAL REPORT FACTS")
    print("=" * 80)

    url_hash = hashlib.sha256(AR_URL.encode()).hexdigest()
    pdf_path = os.path.join(CACHE_DIR, f"{url_hash}.pdf")
    doc = fitz.open(pdf_path)

    raw_facts = [
        {
            "fact_id": "fact_ar_biz_1",
            "section": "business_snapshot",
            "metric": "Industry Position & Nature of Operations",
            "statement": "Kaynes Technology operates predominantly in the business segment of Electronics Manufacturing Services (EMS) providing integrated end-to-end design and manufacturing solutions.",
            "value": "Electronics Manufacturing Services",
            "check_token": "Electronics Manufacturing Services",
            "page": 280,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_biz_2",
            "section": "business_snapshot",
            "metric": "Geographic Revenue Mix (Domestic vs Export)",
            "statement": "Domestic revenue reached ₹32,752.70 Million (~90.3% of total revenue) while Outside India export revenue stood at ₹3,510.84 Million (~9.7%).",
            "value": "₹32,752.70 Million",
            "check_token": "32,752.70",
            "page": 280,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_fin_1",
            "section": "financial_snapshot",
            "metric": "Consolidated Revenue (FY26)",
            "statement": "FY 2025-26 Consolidated Revenue from Operations reached ₹36,263.54 Million, up 33.2% YoY from ₹27,217.52 Million in FY25.",
            "value": "₹36,263.54 Million",
            "check_token": "36,263.54",
            "page": 239,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_fin_2",
            "section": "financial_snapshot",
            "metric": "Profit Before Tax (PBT FY26)",
            "statement": "FY 2025-26 Consolidated Profit Before Tax stood at ₹5,043.14 Million, up from ₹3,716.24 Million in FY25.",
            "value": "₹5,043.14 Million",
            "check_token": "5,043.14",
            "page": 239,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_fin_3",
            "section": "financial_snapshot",
            "metric": "Profit After Tax (PAT FY26)",
            "statement": "FY 2025-26 Consolidated Profit After Tax (PAT) reached ₹3,638.90 Million (~10.0% net margin), up 24.0% YoY from ₹2,934.33 Million.",
            "value": "₹3,638.90 Million",
            "check_token": "3,638.90",
            "page": 239,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_bs_1",
            "section": "balance_sheet",
            "metric": "Total Shareholders' Equity",
            "statement": "Shareholders' Total Equity expanded to ₹47,624.88 Million as of 31st March 2026, up from ₹28,442.32 Million.",
            "value": "₹47,624.88 Million",
            "check_token": "47,624.88",
            "page": 237,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_bs_2",
            "section": "balance_sheet",
            "metric": "Short-Term Borrowings",
            "statement": "Consolidated Short-term borrowings stood at ₹5,379.41 Million as of 31st March 2026.",
            "value": "₹5,379.41 Million",
            "check_token": "5,379.41",
            "page": 238,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_cash_1",
            "section": "cash_quality",
            "metric": "Operating Cash Flow (CFO)",
            "statement": "Net cash from operating activities was negative ₹6,004.04 Million (-₹600.4 Cr) due to large working capital absorption (Receivables increase of ₹10,238.66 Mn).",
            "value": "-₹6,004.04 Million",
            "check_token": "(6,004.04)",
            "page": 240,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_cont_1",
            "section": "contingent_liabilities",
            "metric": "Corporate Guarantees to Subsidiaries",
            "statement": "Corporate Guarantees extended to Subsidiary Companies stood at ₹23,903.60 Million (₹2,390.4 Cr) as of 31st March 2026.",
            "value": "₹23,903.60 Million",
            "check_token": "23,903.60",
            "page": 277,
            "source_url": AR_URL
        },
        {
            "fact_id": "fact_ar_cont_2",
            "section": "contingent_liabilities",
            "metric": "Tax & Performance Guarantees",
            "statement": "Bank Guarantees for contractual performance of ₹1,905.95 Million, Income tax disputes of ₹130.19 Million, and GST disputes of ₹124.82 Million.",
            "value": "₹1,905.95 Million",
            "check_token": "1,905.95",
            "page": 277,
            "source_url": AR_URL
        }
    ]

    verified_facts = []
    for f in raw_facts:
        ok = verify_fact_on_page(doc, f["page"], f["check_token"])
        if ok:
            verified_facts.append(f)
            print(f"VERIFIED [p.{f['page']}]: {f['metric']} = {f['value']}")
        else:
            print(f"DROPPED [p.{f['page']}]: {f['metric']}")

    print(f"Total facts verified: {len(verified_facts)} of {len(raw_facts)}")

    with open(KAYNES_JSON_PATH, "r", encoding="utf-8") as f:
        dossier = json.load(f)

    # Attach fact_id to promised_vs_delivered rows
    for i, p in enumerate(dossier.get("promised_vs_delivered", [])):
        p["fact_id"] = f"fact_guidance_{i+1}"

    dossier["annual_report_facts"] = verified_facts

    # Synthesize with Gemini
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    all_facts = dossier["promised_vs_delivered"] + verified_facts
    feed_facts = [
        {"fact_id": x["fact_id"], "statement": x.get("statement") or x.get("quote"), "metric": x.get("metric")}
        for x in all_facts
    ]

    prompt = f"""You are a senior equity analyst evaluating Kaynes Technology India Limited (KAYNES).
You are provided STRICTLY with the following pre-audited facts. You may NOT cite or introduce outside facts.

Facts Feed:
{json.dumps(feed_facts, indent=2)}

Synthesize:
1. "narrative_vs_numbers": 2 divergence topics comparing management targets with reported numbers (e.g. revenue scale vs negative operating cash flow, domestic concentration).
2. "bull_case": 3 distinct arguments with "title", "argument", "cited_fact_ids" (must use exact fact_ids from above).
3. "bear_case": 3 distinct vulnerabilities with "title", "argument", "cited_fact_ids" (highlighting negative operating cash flow of -₹6,004 Mn and corporate guarantees of ₹23,903 Mn).

Output ONLY JSON:
{{
  "narrative_vs_numbers": [ {{"topic": "...", "management_narrative": "...", "reported_numbers": "...", "divergence_type": "Agrees|Under Observation", "analysis": "...", "cited_fact_ids": ["..."]}} ],
  "bull_case": [ {{"title": "...", "argument": "...", "cited_fact_ids": ["..."]}} ],
  "bear_case": [ {{"title": "...", "argument": "...", "cited_fact_ids": ["..."]}} ]
}}
"""
    model_name = "gemini-3.5-flash-lite"
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
    )

    usage = getattr(resp, "usage_metadata", None)
    in_tok = getattr(usage, "prompt_token_count", 0) or 0
    out_tok = getattr(usage, "candidates_token_count", 0) or 0
    thinking_tok = getattr(usage, "thinking_token_count", 0) or 0
    log_cost("research_synthesis_KAYNES", model_name, in_tok, out_tok, thinking_tok)

    clean_json = re.sub(r"^```json\s*", "", resp.text.strip(), flags=re.MULTILINE)
    clean_json = re.sub(r"\s*```$", "", clean_json.strip(), flags=re.MULTILINE)
    synth = json.loads(clean_json)

    dossier["narrative_vs_numbers"] = synth.get("narrative_vs_numbers", [])
    dossier["bull_case"] = synth.get("bull_case", [])
    dossier["bear_case"] = synth.get("bear_case", [])

    with open(KAYNES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dossier, f, indent=2, ensure_ascii=False)

    print("Successfully enriched KAYNES.json with annual report facts and synthesis!")

if __name__ == "__main__":
    run()
