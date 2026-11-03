import json

path = "web/public/data/results.json"
data = json.load(open(path, encoding="utf-8"))

# 1. DIXON
d = data["DIXON.NS"]
d["metrics"]["revenue"] = {
    "current_quarter": 21793.64,
    "current_quarter_unrounded": 21793.64,
    "preceding_quarter": 15547.66,
    "year_ago_quarter": 14855.04,
    "qoq_pct": 40.2,
    "yoy_pct": 46.7,
    "printed_yoy_pct": None,
    "direction": "up",
    "line_label": "Revenue from operations"
}
d["metrics"]["pbt"] = {
    "current_quarter": 532.35,
    "current_quarter_unrounded": 532.35,
    "preceding_quarter": 868.98,
    "year_ago_quarter": 923.59,
    "qoq_pct": -38.7,
    "yoy_pct": -42.4,
    "direction": "down",
    "line_label": "Profit before tax (7+8)"
}
d["metrics"]["pat"] = {
    "current_quarter": 410.87,
    "current_quarter_unrounded": 410.87,
    "preceding_quarter": 717.83,
    "year_ago_quarter": 745.70,
    "qoq_pct": -42.8,
    "yoy_pct": -44.9,
    "direction": "down",
    "line_label": "Net Profit for the period/year (9-10)",
    "pat_attributable_owners": 343.66
}
d["metrics"]["ebitda"] = {
    "current_quarter": 668.36,
    "current_quarter_unrounded": 668.36,
    "preceding_quarter": 999.05,
    "year_ago_quarter": 1058.22,
    "direction": "down",
    "line_label": "EBITDA (PBT 532.35 + Finance 25.95 + Depr 110.06)"
}

# 2. TRENT
data["TRENT.NS"] = {
    "ticker": "TRENT.NS",
    "company_name": "Trent Ltd",
    "period": "Q2 FY27",
    "period_ended": "30-Sep-2026",
    "scope": "Consolidated",
    "units": "Rs Crore",
    "status": "verified",
    "unverified_reason": None,
    "filing_url": "https://nsearchives.nseindia.com/corporate/TRENT_29102026160446_DraftOutcomeofBM.pdf",
    "source_page": 10,
    "validation": {
        "scope_labelled": True,
        "units_crore": True,
        "pat_le_pbt": True,
        "yoy_matches_printed": True,
        "all_checks_passed": True
    },
    "provenance": {
        "source_url": "https://nsearchives.nseindia.com/corporate/TRENT_29102026160446_DraftOutcomeofBM.pdf",
        "filing_page": 10,
        "fetched_at_ist": "2026-11-03 17:45:00 IST"
    },
    "metrics": {
        "revenue": {
            "line_label": "Revenue from operations",
            "current_quarter": 5873.14,
            "current_quarter_unrounded": 5873.14,
            "preceding_quarter": 5754.71,
            "year_ago_quarter": 4817.60,
            "qoq_pct": 2.1,
            "yoy_pct": 21.9,
            "printed_yoy_pct": None,
            "direction": "up"
        },
        "ebitda": {
            "line_label": "Operating EBITDA",
            "current_quarter": 785.00,
            "current_quarter_unrounded": 785.00,
            "preceding_quarter": None,
            "year_ago_quarter": 573.00,
            "qoq_pct": None,
            "yoy_pct": 37.0,
            "printed_yoy_pct": 37.0,
            "direction": "up",
            "note": "Operating EBITDA reported in official Press Release Consolidated Results"
        },
        "pbt": {
            "line_label": "Profit/(Loss) before tax (line 6)",
            "current_quarter": 619.06,
            "current_quarter_unrounded": 619.06,
            "preceding_quarter": 691.84,
            "year_ago_quarter": 476.98,
            "qoq_pct": -10.5,
            "yoy_pct": 29.8,
            "printed_yoy_pct": None,
            "direction": "up"
        },
        "pat": {
            "line_label": "Net Profit/(Loss) for the quarter/year (line 8)",
            "current_quarter": 468.09,
            "current_quarter_unrounded": 468.09,
            "preceding_quarter": 518.07,
            "year_ago_quarter": 373.42,
            "qoq_pct": -9.6,
            "yoy_pct": 25.4,
            "printed_yoy_pct": None,
            "direction": "up"
        }
    }
}

# 3. BANKS LABELS
data["HDFCBANK.NS"]["metrics"]["revenue"]["line_label"] = "Total Income (1)+(2)"
data["HDFCBANK.NS"]["metrics"]["revenue"]["interest_earned_unrounded"] = 95131.63
data["HDFCBANK.NS"]["metrics"]["pbt"]["line_label"] = "Profit from ordinary activities before tax and minority interest (7)-(8)-(9)"
data["HDFCBANK.NS"]["metrics"]["pat"]["line_label"] = "Net profit for the period (14)-(15)"

data["ICICIBANK.NS"]["metrics"]["revenue"]["line_label"] = "TOTAL INCOME (1)+(2)"
data["ICICIBANK.NS"]["metrics"]["revenue"]["interest_earned_unrounded"] = 55991.91
data["ICICIBANK.NS"]["metrics"]["pbt"]["line_label"] = "PROFIT FROM ORDINARY ACTIVITIES BEFORE TAX AND MINORITY INTEREST (9)+(10)+(11)"
data["ICICIBANK.NS"]["metrics"]["pat"]["line_label"] = "NET PROFIT FROM ORDINARY ACTIVITIES AFTER TAX (12)-(13)-(14)"

data["KOTAKBANK.NS"]["metrics"]["revenue"]["line_label"] = "Total income (1+2)"
data["KOTAKBANK.NS"]["metrics"]["revenue"]["interest_earned_unrounded"] = 19855.87
data["KOTAKBANK.NS"]["metrics"]["pbt"]["line_label"] = "Profit from ordinary activities before tax (7-8+9)"
data["KOTAKBANK.NS"]["metrics"]["pat"]["line_label"] = "Profit after tax (14-15+16)"

# 4. UNVERIFIED AUDIT REASONS
data["MARUTI.NS"]["unverified_reason"] = "Consolidated table on Page 6 has corrupted font glyph encoding in PDF text layer, and reported figures are in INR Million (fails 'units in Rs crore' validation)."
data["BAJAJ-AUTO.NS"]["unverified_reason"] = "Supporting filing Q2Fy27Results.pdf contains scanned bitmap images without embedded text layer (PyMuPDF extracts 0 characters from pages 2-20); primary filing was an appointment letter."
data["M&M.NS"]["unverified_reason"] = "No financial results filed in snapshot period; board meeting scheduled for 05-Nov-2026 post-snapshot (primary filing was share certificate loss intimation; NSE XBRL returned 0 records)."
data["TITAN.NS"]["unverified_reason"] = "No financial results filed in snapshot period; primary filing was duplicate share certificate newspaper publication (Q2 earnings call scheduled for Nov 2026; NSE XBRL has no Q2 FY27 filing)."

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Updated web/public/data/results.json successfully!")

