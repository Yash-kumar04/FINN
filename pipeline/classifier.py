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

Multi-label output:
- primary_category (str)
- secondary_tags (List[str])
- is_supporting_doc (bool)

Explicit Rules:
- transcript / recording / audio -> primary: earnings_call, even if mentioning results
- investor presentation filed with results -> primary: results, tag: investor_presentation
- newspaper publication of results -> primary: results, is_supporting_doc: True, tag: supporting_doc
- board outcome with results + appointment -> primary: results, tag: management_change
"""

from typing import Dict, Any, List

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

def classify_announcement(desc: str, attchmnt_text: str) -> Dict[str, Any]:
    """
    Classifies an announcement into primary_category, secondary_tags, and is_supporting_doc.
    """
    d = (desc or "").lower()
    t = (attchmnt_text or "").lower()
    combined = d + " " + t

    secondary_tags = set()
    is_supporting_doc = False

    # Check specific keyword buckets
    has_transcript_audio = any(k in combined for k in [
        "transcript", "audio recording", "link of recording", "recording of earnings",
        "concall recording", "conference call recording", "webcast link"
    ])
    
    has_results = any(k in combined for k in [
        "financial result", "financial results", "quarterly result", "half yearly result",
        "unaudited financial", "audited financial", "period ended september", "period ended december",
        "period ended march", "period ended june", "outcome of board meeting"
    ])
    
    has_presentation = any(k in combined for k in [
        "investor presentation", "earnings presentation", "presentation on financial",
        "analyst presentation"
    ])
    
    has_newspaper = any(k in combined for k in [
        "newspaper publication", "newspaper advertisement", "publication in newspaper"
    ])
    
    has_mgmt_change = (
        "change in management" in combined or
        "change in director" in combined or
        "retirement" in combined or
        "superannuation" in combined or
        any(k in combined for k in [
            "appointment of director", "resignation of director", "cessation of director",
            "appointment of additional director", "executive director", "independent director",
            "appointment of chief", "resignation of chief", "appointment of ceo", "resignation of ceo",
            "appointment of cfo", "resignation of cfo", "managing director", "whole-time director",
            "key managerial personnel", "re-appointment", "appointment of ms", "appointment of mr",
            "appointment of shri", "appointment of dr"
        ]) or
        (("appointment" in combined or "resignation" in combined or "cessation" in combined or "re-appointment" in combined or "retirement" in combined) and
         any(k in combined for k in ["director", "kmp", "chief", "officer", "ceo", "cfo", "managing director", "president", "chairman", "vice president", "senior vice president"])) or
        (d.strip() in ["appointment", "retirement", "resignation", "cessation"])
    )

    has_m_and_a = any(k in combined for k in [
        "acquisition", "merger", "demerger", "joint venture", "amalgamation",
        "scheme of arrangement", "slump sale", "business transfer", "investing in subsidiary",
        "wholly owned subsidiary", "incorporation of subsidiary", "sale of stake", "divestment",
        "strike off", "sale or disposal"
    ])

    has_fund_raise = (
        any(k in combined for k in [
            "fund raise", "fund raising", "rights issue", "qip", "qualified institutions placement",
            "preferential allotment", "buyback", "commercial paper", "ncd issue",
            "non-convertible debentures", "allotment of equity shares", "allotment of securities"
        ]) and not any(k in combined for k in ["esop", "stock option", "esps", "esos"])
    )

    has_litigation = any(k in combined for k in [
        "litigation", "lawsuit", "court order", "nclt", "nclat", "penalty", "adjudication",
        "show cause notice", "regulatory order", "sebi order", "tax order", "tax demand",
        "corporate insolvency resolution process", "cirp", "action(s) taken or orders passed"
    ])

    has_credit_rating = any(k in combined for k in [
        "credit rating", "rating assigned", "rating reaffirmed", "rating upgraded",
        "rating downgraded", "crisil", "icra", "care rating", "india ratings"
    ])

    has_dividend = any(k in combined for k in [
        "dividend", "interim dividend", "final dividend", "declaration of dividend"
    ])

    has_investor_meet = any(k in combined for k in [
        "schedule of meet", "schedule of analyst", "schedule of institutional",
        "analyst meet", "institutional investor meet", "investor conference", "interaction with",
        "investor(s) meet", "analyst(s)"
    ])

    has_press_release = any(k in combined for k in [
        "press release", "media release", "monthly business updates", "business updates",
        "order win", "new product", "bagging/receiving of orders", "receiving of orders",
        "orders/contracts", "rumour verification", "news verification", "clarification on news"
    ])

    has_postal_ballot = "postal ballot" in combined
    has_agm_egm = any(k in combined for k in ["annual general meeting", "extraordinary general meeting", "notice of agm"])
    has_pledging = any(k in combined for k in ["pledge", "encumbrance"])
    
    has_routine = any(k in combined for k in [
        "esop", "stock option", "transfer of equity shares", "compliance certificate",
        "regulation 74(5)", "regulation 40(9)", "regulation 7(3)", "regulation 13(3)",
        "guarantee", "loss of share certificate", "duplicate share", "secretarial"
    ])

    # -------------------------------------------------------------------------
    # RULE 1: Transcript/recording/audio -> earnings_call even if mentioning results
    # -------------------------------------------------------------------------
    if has_transcript_audio:
        primary = "earnings_call"
        if has_results:
            secondary_tags.add("results")
        if has_presentation:
            secondary_tags.add("investor_presentation")
        return {
            "category": primary,
            "secondary_tags": sorted(list(secondary_tags)),
            "is_supporting_doc": False,
            "importance_weight": CATEGORY_WEIGHTS["earnings_call"],
            "tier": 2
        }

    # -------------------------------------------------------------------------
    # RULE 2: Newspaper publication of results -> results but flagged supporting_doc
    # -------------------------------------------------------------------------
    if has_newspaper and has_results:
        primary = "results"
        is_supporting_doc = True
        secondary_tags.add("supporting_doc")
        secondary_tags.add("newspaper_ad")
        return {
            "category": primary,
            "secondary_tags": sorted(list(secondary_tags)),
            "is_supporting_doc": True,
            "importance_weight": CATEGORY_WEIGHTS["results"],
            "tier": 1
        }

    # -------------------------------------------------------------------------
    # RULE 3: Investor presentation filed with results -> results
    # -------------------------------------------------------------------------
    if has_presentation and (has_results or "outcome" in combined):
        primary = "results"
        secondary_tags.add("investor_presentation")
        return {
            "category": primary,
            "secondary_tags": sorted(list(secondary_tags)),
            "is_supporting_doc": False,
            "importance_weight": CATEGORY_WEIGHTS["results"],
            "tier": 1
        }

    # -------------------------------------------------------------------------
    # RULE 4: Board outcome with results + appointment -> primary results, tag mgmt_change
    # -------------------------------------------------------------------------
    if has_results and has_mgmt_change:
        primary = "results"
        secondary_tags.add("management_change")
        if has_dividend:
            secondary_tags.add("dividend")
        return {
            "category": primary,
            "secondary_tags": sorted(list(secondary_tags)),
            "is_supporting_doc": False,
            "importance_weight": CATEGORY_WEIGHTS["results"],
            "tier": 1
        }

    # -------------------------------------------------------------------------
    # Standard Priority Cascade for other filings
    # -------------------------------------------------------------------------
    if has_results:
        primary = "results"
        if has_dividend:
            secondary_tags.add("dividend")
    elif has_mgmt_change:
        primary = "management_change"
    elif has_m_and_a:
        primary = "M&A"
    elif has_fund_raise:
        primary = "fund_raise"
    elif has_litigation:
        primary = "litigation"
    elif has_credit_rating:
        primary = "credit_rating"
    elif has_dividend:
        primary = "dividend"
    elif has_presentation:
        primary = "press_release"
        secondary_tags.add("investor_presentation")
    elif has_press_release:
        primary = "press_release"
    elif has_investor_meet:
        primary = "investor_meetings"
    elif has_postal_ballot:
        primary = "postal_ballot"
    elif has_agm_egm:
        primary = "agm_egm"
    elif has_pledging:
        primary = "pledging"
    elif has_newspaper:
        primary = "unclassified"
        is_supporting_doc = True
        secondary_tags.add("newspaper_ad")
    elif has_routine:
        primary = "unclassified"
        if "esop" in combined or "stock option" in combined:
            secondary_tags.add("esop")
    else:
        primary = "unclassified"

    # Tier mapping
    if primary in ["results", "management_change", "M&A", "fund_raise", "litigation", "capex"]:
        tier = 1
    elif primary in ["credit_rating", "dividend", "bonus_split", "insider_trading", "earnings_call", "press_release", "investor_meetings"]:
        tier = 2
    else:
        tier = 3

    return {
        "category": primary,
        "secondary_tags": sorted(list(secondary_tags)),
        "is_supporting_doc": is_supporting_doc,
        "importance_weight": CATEGORY_WEIGHTS.get(primary, 0.1),
        "tier": tier
    }
