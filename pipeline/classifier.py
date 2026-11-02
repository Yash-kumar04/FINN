"""
pipeline/classifier.py
Rules-based announcement classifier implementing the exact 17 categories from reference.pdf:
1. results
2. M&A
3. fund_raise
4. management_change
5. litigation
6. insider_trading
7. earnings_call
8. investor_meetings
9. credit_rating
10. dividend
11. bonus_split
12. capex
13. press_release
14. postal_ballot
15. agm_egm
16. pledging
17. unclassified

No LLM calls. Rules-based on `desc` + `attchmntText`.
"""

import re
from typing import Dict, Any, List

# Exact 17 categories in priority order for conflict resolution
# Higher priority categories come first when resolving ambiguities
CATEGORY_PRIORITY = [
    "results",
    "management_change",
    "M&A",
    "fund_raise",
    "litigation",
    "capex",
    "dividend",
    "bonus_split",
    "credit_rating",
    "insider_trading",
    "earnings_call",
    "investor_meetings",
    "press_release",
    "postal_ballot",
    "agm_egm",
    "pledging",
    "unclassified"
]

# Importance weight for each category (used in FINN importance scoring)
CATEGORY_WEIGHTS = {
    "results": 1.0,
    "management_change": 0.9,
    "M&A": 0.9,
    "fund_raise": 0.85,
    "litigation": 0.8,
    "capex": 0.75,
    "credit_rating": 0.65,
    "dividend": 0.6,
    "bonus_split": 0.6,
    "insider_trading": 0.55,
    "earnings_call": 0.5,
    "press_release": 0.45,
    "investor_meetings": 0.35,
    "postal_ballot": 0.3,
    "agm_egm": 0.3,
    "pledging": 0.4,
    "unclassified": 0.1
}

# Rule matchers: mapping category -> function(desc_lower, text_lower) -> bool
def match_results(d: str, t: str) -> bool:
    # Results, board meeting approving results, results deck, ads confirming results
    if any(k in d for k in [
        "financial result", "financial results", "outcome of board meeting",
        "unaudited financial", "audited financial", "quarterly result", "half yearly result"
    ]):
        return True
    if any(k in t for k in [
        "financial results", "financial result", "un-audited financial results",
        "unaudited financial results", "audited financial results", "statement of standalone",
        "statement of consolidated", "period ended september", "period ended december",
        "period ended march", "period ended june", "newspaper publication of unaudited",
        "newspaper publication of financial"
    ]):
        return True
    return False

def match_m_and_a(d: str, t: str) -> bool:
    # Acquisition, merger, demerger, JV, investing in/selling stake in subsidiary
    combined = d + " " + t
    if any(k in combined for k in [
        "acquisition", "merger", "demerger", "joint venture", "amalgamation",
        "scheme of arrangement", "slump sale", "business transfer", "investing in subsidiary",
        "sale of stake", "divestment", "hiving off"
    ]):
        return True
    return False

def match_fund_raise(d: str, t: str) -> bool:
    # Raising money from outside investors - rights, QIP, preferential, buyback, CP, NCD
    combined = d + " " + t
    if any(k in combined for k in [
        "fund raise", "fund raising", "rights issue", "qip", "qualified institutions placement",
        "preferential allotment", "buyback", "commercial paper", "ncd issue",
        "non-convertible debentures", "allotment of equity shares", "allotment of securities"
    ]):
        # Distinguish from ESOP allotment
        if "esop" not in combined and "stock option" not in combined:
            return True
    return False

def match_management_change(d: str, t: str) -> bool:
    # Change at top - CEO, CFO, MD, Director joining, resigning, retiring
    combined = d + " " + t
    if "change in management" in d or "change in management" in t:
        return True
    if any(k in combined for k in [
        "appointment of director", "resignation of director", "cessation of director",
        "appointment of chief executive", "resignation of chief executive", "appointment of ceo",
        "resignation of ceo", "appointment of cfo", "resignation of cfo", "appointment of managing director",
        "resignation of managing director", "appointment of executive director",
        "key managerial personnel", "kmp appointment", "re-appointment of director"
    ]):
        return True
    return False

def match_litigation(d: str, t: str) -> bool:
    # Lawsuits, regulatory orders, fines, warnings, insolvency/restructuring
    combined = d + " " + t
    return any(k in combined for k in [
        "litigation", "lawsuit", "court order", "nclt", "penalty", "adjudication",
        "show cause notice", "regulatory order", "sebi order", "tax order",
        "tax demand", "arbitration", "restructuring proceedings", "insolvency"
    ])

def match_insider_trading(d: str, t: str) -> bool:
    # Promoter or insider buying/selling their own shares
    combined = d + " " + t
    return any(k in combined for k in [
        "insider trading", "regulation 7(2)", "sast", "promoter acquisition",
        "promoter sale", "disclosures under sebi (pit)", "pit regulations"
    ])

def match_earnings_call(d: str, t: str) -> bool:
    # Earnings call transcript, recording link, audio, concall notice
    combined = d + " " + t
    if any(k in combined for k in [
        "transcript of earning", "earnings call transcript", "concall transcript",
        "link of recording", "audio recording", "recording of earnings", "concall recording",
        "conference call recording", "webcast link"
    ]):
        return True
    if "conference call" in combined and any(k in combined for k in ["transcript", "audio", "recording"]):
        return True
    return False

def match_investor_meetings(d: str, t: str) -> bool:
    # One-on-one or small group meetings, investor conference schedule
    combined = d + " " + t
    if any(k in combined for k in [
        "schedule of meet", "schedule of analyst", "schedule of institutional",
        "analyst meet", "institutional investor meet", "investor conference",
        "interaction with institutional", "meeting with fund"
    ]):
        # If it's the recording or transcript, earnings_call takes precedence
        if not any(k in combined for k in ["transcript", "recording", "audio"]):
            return True
    return False

def match_credit_rating(d: str, t: str) -> bool:
    combined = d + " " + t
    return any(k in combined for k in [
        "credit rating", "rating assigned", "rating reaffirmed", "rating upgraded",
        "rating downgraded", "crisil", "icra", "care rating", "india ratings", "fitch"
    ])

def match_dividend(d: str, t: str) -> bool:
    combined = d + " " + t
    return any(k in combined for k in [
        "interim dividend", "final dividend", "declaration of dividend",
        "dividend recommended", "record date for dividend"
    ])

def match_bonus_split(d: str, t: str) -> bool:
    combined = d + " " + t
    return any(k in combined for k in [
        "bonus issue", "bonus shares", "stock split", "sub-division of shares",
        "subdivision of shares", "split of face value"
    ])

def match_capex(d: str, t: str) -> bool:
    combined = d + " " + t
    return any(k in combined for k in [
        "capacity expansion", "capital expenditure", "capex", "new plant",
        "new manufacturing facility", "setting up of new facility", "commissioning of",
        "greenfield facility"
    ])

def match_press_release(d: str, t: str) -> bool:
    combined = d + " " + t
    return any(k in combined for k in [
        "press release", "media release", "business updates", "monthly business updates",
        "order win", "new product launch", "partnership", "investor presentation"
    ])

def match_postal_ballot(d: str, t: str) -> bool:
    combined = d + " " + t
    return "postal ballot" in combined

def match_agm_egm(d: str, t: str) -> bool:
    combined = d + " " + t
    return any(k in combined for k in [
        "annual general meeting", "extraordinary general meeting", "notice of agm",
        "notice of egm", "proceedings of agm", "voting results of agm"
    ])

def match_pledging(d: str, t: str) -> bool:
    combined = d + " " + t
    return any(k in combined for k in [
        "pledge of shares", "encumbrance of shares", "release of pledge",
        "invocation of pledge", "pledging"
    ])

def match_unclassified_routine(d: str, t: str) -> bool:
    combined = d + " " + t
    return any(k in combined for k in [
        "esop", "stock option", "transfer of equity shares by", "employees stock option",
        "compliance certificate", "certificate under reg", "regulation 74(5)",
        "regulation 40(9)", "regulation 7(3)", "regulation 13(3)",
        "guarantee", "loss of share certificate", "duplicate share",
        "newspaper publication", "clarification", "updates"
    ])

# Table of matchers
RULE_MATCHERS = [
    ("results", match_results),
    ("management_change", match_management_change),
    ("M&A", match_m_and_a),
    ("fund_raise", match_fund_raise),
    ("litigation", match_litigation),
    ("insider_trading", match_insider_trading),
    ("earnings_call", match_earnings_call),
    ("investor_meetings", match_investor_meetings),
    ("credit_rating", match_credit_rating),
    ("dividend", match_dividend),
    ("bonus_split", match_bonus_split),
    ("capex", match_capex),
    ("press_release", match_press_release),
    ("postal_ballot", match_postal_ballot),
    ("agm_egm", match_agm_egm),
    ("pledging", match_pledging),
    ("unclassified", match_unclassified_routine),
]


def classify_announcement(desc: str, attchmnt_text: str) -> Dict[str, Any]:
    """
    Classifies an announcement using rules into the 17 categories.
    Returns:
    {
        "category": str,
        "is_ambiguous": bool,
        "matched_categories": List[str],
        "importance_weight": float,
        "tier": int (1: actionable, 2: informational, 3: routine)
    }
    """
    d = (desc or "").lower()
    t = (attchmnt_text or "").lower()

    matches = []
    for cat, matcher in RULE_MATCHERS:
        try:
            if matcher(d, t):
                matches.append(cat)
        except Exception:
            pass

    if not matches:
        return {
            "category": "unclassified",
            "is_ambiguous": False,
            "matched_categories": ["unclassified"],
            "importance_weight": CATEGORY_WEIGHTS["unclassified"],
            "tier": 3
        }

    # Resolve ambiguity using explicit category priority
    resolved_category = None
    for p_cat in CATEGORY_PRIORITY:
        if p_cat in matches:
            resolved_category = p_cat
            break

    if not resolved_category:
        resolved_category = matches[0]

    # Map tier
    if resolved_category in ["results", "management_change", "M&A", "fund_raise", "litigation", "capex"]:
        tier = 1
    elif resolved_category in ["credit_rating", "dividend", "bonus_split", "insider_trading", "earnings_call", "press_release", "investor_meetings"]:
        tier = 2
    else:
        tier = 3

    return {
        "category": resolved_category,
        "is_ambiguous": len(matches) > 1,
        "matched_categories": matches,
        "importance_weight": CATEGORY_WEIGHTS.get(resolved_category, 0.2),
        "tier": tier
    }
