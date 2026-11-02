"""
pipeline/fetch_announcements.py
Fetches 30-day corporate announcements for all 19 portfolio tickers.

Rules:
- NSE per symbol, last 30 days (URL-encode M&M).
- BSE scrip endpoint (curl_cffi) as fallback.
- Dedupe by seq_id.
- Keep raw fields and the attachment URL.
- Record provenance: source, fetched_at_ist, as_of_date.
- If source fails, mark source_unavailable; never silently drop.
- Classify with rules into the 17 reference categories.
- Report category histogram and ambiguity count.
- Writes to web/public/data/announcements.json
"""

import os
import sys

# Ensure UTF-8 output on Windows PowerShell
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import time
import urllib.parse
from datetime import datetime, timedelta
import pytz
import requests
from dotenv import load_dotenv

from classifier import classify_announcement, CATEGORY_WEIGHTS
from fetch_prices import PORTFOLIO

load_dotenv()
IST = pytz.timezone("Asia/Kolkata")

BSE_SCRIP_CODES = {
    "RELIANCE.NS": "500325",
    "LT.NS": "500510",
    "HDFCBANK.NS": "500180",
    "ICICIBANK.NS": "532174",
    "KOTAKBANK.NS": "500247",
    "TCS.NS": "532540",
    "INFY.NS": "500209",
    "MARUTI.NS": "532500",
    "M&M.NS": "500520",
    "BAJAJ-AUTO.NS": "532977",
    "DIXON.NS": "540699",
    "KAYNES.NS": "543910",
    "POLYCAB.NS": "542652",
    "HAL.NS": "541154",
    "BEL.NS": "500049",
    "TRENT.NS": "500251",
    "TITAN.NS": "500114",
    "SUNPHARMA.NS": "524715",
    "CDSL.NS": "543232",
}

def create_nse_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
    })
    try:
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(0.5)
    except Exception as e:
        print(f"  [NSE Cookie Session Init]: {e}")
    return session


def fetch_nse_announcements_for_symbol(session, symbol, days=30):
    """
    Fetch last 30-day announcements for an individual symbol from NSE.
    Encodes M&M properly as M%26M.
    """
    clean_sym = symbol.replace(".NS", "")
    encoded_sym = urllib.parse.quote(clean_sym)
    
    to_date = datetime.now(IST)
    from_date = to_date - timedelta(days=days)
    from_str = from_date.strftime("%d-%m-%Y")
    to_str = to_date.strftime("%d-%m-%Y")

    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={encoded_sym}&from_date={from_str}&to_date={to_str}"
    
    try:
        r = session.get(url, timeout=12)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return {"status": "ok", "records": data}
            return {"status": "error", "error": f"Unexpected JSON response: {type(data)}"}
        return {"status": "error", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def fetch_bse_fallback(scrip_code):
    """
    BSE Scrip-specific fallback endpoint using curl_cffi.
    """
    if not scrip_code:
        return {"status": "error", "error": "No BSE scrip code"}
    try:
        from curl_cffi import requests as curl_requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bseindia.com/corporates/ann.html",
            "Origin": "https://www.bseindia.com"
        }
        url = f"https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?pageno=1&strCat=-1&strPrevDate=&strScrip={scrip_code}&strSearch=P&strToDate=&strType=C"
        r = curl_requests.get(url, headers=headers, impersonate="chrome124", timeout=10)
        if r.status_code == 200:
            data = r.json()
            table = data.get("Table", [])
            return {"status": "ok", "records": table}
        return {"status": "error", "error": f"BSE HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "error": f"BSE fallback exception: {e}"}


def fetch_and_classify_all():
    now_ist = datetime.now(IST)
    fetched_at_str = now_ist.isoformat()

    print(f"\nInitializing Announcements Pipeline at {fetched_at_str}...")
    session = create_nse_session()

    ticker_results = {}
    all_classified_announcements = []

    category_histogram = {cat: 0 for cat in CATEGORY_WEIGHTS.keys()}
    ambiguous_count = 0
    total_deduped_announcements = 0

    # Load prices to compute market reaction multiplier if available
    prices_data = {}
    try:
        with open("web/public/data/prices.json", "r", encoding="utf-8") as f:
            p_json = json.load(f)
            prices_data = p_json.get("tickers", {})
    except Exception:
        pass

    for item in PORTFOLIO:
        sym = item["symbol"]
        clean_sym = sym.replace(".NS", "")
        scrip = BSE_SCRIP_CODES.get(sym, "")
        p_weight = item["weight"]

        # Fetch market metrics for this ticker
        ticker_price = prices_data.get(sym, {}).get("metrics", {})
        price_chg = abs(ticker_price.get("price_change_pct", 0.0))
        vol_ratio = ticker_price.get("volume_ratio", 1.0)
        
        # Reaction multiplier: higher if volume or price moved significantly
        reaction_multiplier = 1.0 + (min(vol_ratio, 4.0) - 1.0) * 0.15 + (min(price_chg, 10.0)) * 0.05

        print(f"  Fetching announcements for {sym:<16}...", end=" ", flush=True)

        nse_res = fetch_nse_announcements_for_symbol(session, sym, days=30)
        raw_records = []
        source_used = "nse"

        if nse_res["status"] == "ok":
            raw_records = nse_res["records"]
            print(f"✅ NSE OK ({len(raw_records)} items)", end=" ")
        else:
            print(f"⚠️ NSE failed ({nse_res['error']}) -> Trying BSE...", end=" ")
            bse_res = fetch_bse_fallback(scrip)
            if bse_res["status"] == "ok":
                source_used = "bse_fallback"
                raw_records = bse_res["records"]
                print(f"✅ BSE OK ({len(raw_records)} items)", end=" ")
            else:
                source_used = "source_unavailable"
                print(f"❌ BSE also failed ({bse_res['error']})", end=" ")

        # Dedupe by seq_id (or BSE composite key)
        seen_keys = set()
        deduped_records = []

        for r in raw_records:
            if source_used == "nse":
                dedup_key = str(r.get("seq_id", "")) or str(r.get("dt", ""))
                desc = r.get("desc", "") or ""
                att_text = r.get("attchmntText", "") or ""
                att_url = r.get("attchmntFile") or None
                time_str = r.get("an_dt", "")
            else:
                dedup_key = str(r.get("NEWS_DT", "")) + "_" + str(r.get("SCRIP_CD", ""))
                desc = r.get("CATEGORYNAME", "") or ""
                att_text = r.get("NEWSSUB", "") or ""
                att_file = r.get("ATTACHMENTNAME", "")
                att_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{att_file}" if att_file else None
                time_str = r.get("NEWS_DT", "")

            if not dedup_key or dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            # Classify using reference categories
            cls_result = classify_announcement(desc, att_text)
            cat = cls_result["category"]
            category_histogram[cat] = category_histogram.get(cat, 0) + 1

            if cls_result["is_ambiguous"]:
                ambiguous_count += 1

            # Rules-based importance score
            cat_weight = cls_result["importance_weight"]
            importance_score = round(cat_weight * p_weight * reaction_multiplier * 100.0, 2)

            # Generate explicit one-line 'Why you should care'
            why_care = generate_why_you_should_care(cat, desc, att_text, item["name"], ticker_price)

            classified_record = {
                "ticker": sym,
                "company_name": item["name"],
                "seq_id": dedup_key,
                "timestamp": time_str,
                "desc": desc,
                "attachment_text": att_text,
                "attachment_url": att_url,
                "classification": cls_result,
                "importance_score": importance_score,
                "why_you_should_care": why_care,
                "raw_record": r,
                "provenance": {
                    "source": source_used,
                    "fetched_at_ist": fetched_at_str
                }
            }
            deduped_records.append(classified_record)
            all_classified_announcements.append(classified_record)

        total_deduped_announcements += len(deduped_records)
        print(f"-> {len(deduped_records)} unique records")

        ticker_results[sym] = {
            "symbol": sym,
            "name": item["name"],
            "status": "ok" if source_used != "source_unavailable" else "source_unavailable",
            "source": source_used,
            "fetched_at_ist": fetched_at_str,
            "record_count": len(deduped_records),
            "announcements": deduped_records
        }
        time.sleep(0.3)

    # Sort all announcements by importance_score descending
    all_classified_announcements.sort(key=lambda x: x["importance_score"], reverse=True)

    snapshot = {
        "dataset": "portfolio_announcements",
        "provenance": {
            "source": "nse_primary_bse_fallback",
            "fetched_at_ist": fetched_at_str,
            "window_days": 30,
            "portfolio_size": len(PORTFOLIO)
        },
        "stats": {
            "total_announcements": total_deduped_announcements,
            "total_tickers_ok": sum(1 for v in ticker_results.values() if v["status"] == "ok"),
            "total_tickers_unavailable": sum(1 for v in ticker_results.values() if v["status"] == "source_unavailable"),
            "ambiguous_record_count": ambiguous_count,
            "ambiguous_percentage": round((ambiguous_count / total_deduped_announcements * 100.0) if total_deduped_announcements else 0, 2),
            "category_histogram": category_histogram
        },
        "tickers": ticker_results,
        "feed": all_classified_announcements
    }

    out_file = "web/public/data/announcements.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    print(f"\nSaved announcements snapshot to {out_file}")
    return snapshot


def generate_why_you_should_care(cat: str, desc: str, text: str, company: str, metrics: dict) -> str:
    """
    Rules-based 1-line 'why you should care' per card.
    Strictly factual; never invents causation ('rose because').
    """
    vol = metrics.get("volume_ratio", 1.0)
    chg = metrics.get("price_change_pct", 0.0)

    if cat == "results":
        return f"Primary quarterly financial disclosure for {company}; review revenue growth, EBITDA margin trajectory, and profit after tax."
    elif cat == "management_change":
        return f"Leadership transition at {company}; executive appointments or resignations signal changes in capital allocation or strategy."
    elif cat == "M&A":
        return f"Inorganic expansion or stake divestment altering business portfolio scope and consolidated balance sheet."
    elif cat == "fund_raise":
        return f"Capital raise or equity dilution impact on shareholder value and debt leverage profile."
    elif cat == "litigation":
        return f"Legal, regulatory, or tax order with potential contingent liability or operational disruption risk."
    elif cat == "capex":
        return f"Capacity expansion decision affecting multi-year cash flows and future revenue runway."
    elif cat == "dividend":
        return f"Direct cash return to shareholders; check record date and cash outflow impact."
    elif cat == "bonus_split":
        return f"Share capital restructuring modifying liquidity and face value per share."
    elif cat == "credit_rating":
        return f"External rating agency assessment of balance sheet solvency and borrowing costs."
    elif cat == "earnings_call":
        return f"Direct management earnings conference call audio/transcript; primary source for forward operational guidance."
    elif cat == "investor_meetings":
        return f"Institutional fund interaction schedule; potential for discussion on ongoing sector trends."
    elif cat == "press_release":
        return f"Commercial operational update or product milestone disclosed by management."
    elif cat == "unclassified":
        return f"Routine administrative filing (compliance certificate, ESOP transfer, or statutory notice)."
    else:
        return f"Corporate disclosure filed with the stock exchange by {company}."


if __name__ == "__main__":
    fetch_and_classify_all()
