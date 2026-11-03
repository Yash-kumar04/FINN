# FINN: Autonomous Financial Intelligence Platform

> **Mobile-first, dense, anti-hallucinatory intelligence for Indian institutional equity portfolios.**  
> Built for the **ENAM - IIT Screening Assessment 2027**.

---

## 1. Overview & Core Philosophy

Equity analysts spend 80% of their mornings filtering corporate announcements and verifying management claims against regulatory filings. **FINN** automates this workflow with a dual-modal paradigm:
1. **Push Intelligence (The Briefing Tab)**:
   - Evaluates portfolio filings over 3D, 7D, and 30D horizons.
   - Computes deterministic **Importance Scores (0–100)** incorporating portfolio weight, announcement tiering, and market reaction multipliers (+3% move, 2x volume spikes).
   - Surfaces **Verified Results Cards** (Revenue, EBITDA, PBT, PAT with QoQ and YoY pills) and **Management Change Cards** extracted directly from primary PDF filings.
   - Dynamic real-time alerts stack with configurable category checkboxes and volume/price sliders.
2. **Pull Deep Research (The Research Tab)**:
   - Generates comprehensive company research dossiers across 5 quarters of earnings calls and Integrated Annual Reports.
   - Hero **Promised vs. Delivered Scorecard**: Evaluates management guidance with strict metric alignment (*revenue growth is never conflated with volume growth*).
   - **Annual Report Reality**: Extracts 5-year CAGR, segmental mix, balance sheet liquidity (negative net debt), cash quality (108% CFO-to-PAT conversion), and contingent liabilities (DRI customs claims).
   - **Narrative vs. Numbers Reality Check**: Highlights empirical divergences between management optimism and filed financial numbers.
   - **Audited Bull vs. Bear Cases**: Generates 3 bull pillars and 3 bear vulnerabilities where every single argument cites a verified primary fact ID.

---

## 2. System Architecture

FINN is built on a **Snapshot-First, Decoupled Architecture**:
```
┌────────────────────────────────────────────────────────┐
│              Primary Sources & Filings                 │
│   NSE / BSE Regulatory Filings · Screener · Reports    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            Python Ingestion & Audit Pipeline           │
│   - PyMuPDF text & table extraction per page           │
│   - Deterministic Regex & Rule-based extraction        │
│   - Flash Lite minimal thinking for entity extraction  │
│   - In-code substring & numerical assertion audits     │
│   - Cost logging (pipeline/logs/cost_log.json)         │
└──────────────────────────┬─────────────────────────────┘
                           │ Writes static audit JSONs
                           ▼
┌────────────────────────────────────────────────────────┐
│           Public Snapshot Storage (JSON)               │
│   web/public/data/events.json, results.json,           │
│   management.json, research/{TICKER}.json              │
└──────────────────────────┬─────────────────────────────┘
                           │ Read directly / via API
                           ▼
┌────────────────────────────────────────────────────────┐
│            FastAPI Backend (pipeline/api.py)           │
│   - GET /health                                        │
│   - GET /research/{ticker} (cache hit or background)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│              Vite + React Frontend (web/)              │
│   - Mobile-first, dense institutional design           │
│   - Zero invented numbers; displays 'unverified'       │
│   - Tappable page citations linked to primary PDFs     │
└────────────────────────────────────────────────────────┘
```

---

## 3. Provenance & Anti-Hallucination Design

Standing institutional rule: **Never type, estimate, or invent data.** Every figure traces to an audited source with URL, page number, and IST timestamp.

1. **Strict Verbatim Substring Audits**:
   - Every concall quote cited in the Promised vs. Delivered matrix is programmatically verified as an exact substring of the PDF text (`span in page_text == True`). Any extraction failing this check is dropped.
2. **Deterministic Mathematical Assertions**:
   - Quarterly Results Validation: Requires `PAT <= PBT`, units normalized in ₹ Crore, scope explicitly labelled as Consolidated, and computed YoY % matching the company's printed YoY %. If any check fails, the card displays `status: "unverified"` and hides headline numbers.
3. **Strict Metric Alignment Rule**:
   - Management promises are compared **only** against like-for-like delivered metrics. Revenue growth is **never** accepted as fulfillment of a volume promise (e.g. Dixon's 20–25% volume target vs +36.0% revenue growth is marked `Unclear` because price/mix dynamics diverge from physical units).
4. **Primary Sourcing Only**:
   - No external news articles, unverified broker notes, or synthetic LLM hallucinations are permitted. Research draws exclusively from BSE/NSE corporate disclosures and Annual Reports.

---

## 4. Importance Scoring & Ranking Formula

Events in the **Briefing Tab** are prioritized using a deterministic institutional formula:
$$\text{Importance Score} = \min(100, \; (\text{Base Tier Score} + \text{Portfolio Weight Boost}) \times \text{Market Multiplier})$$

- **Base Tier Score**:
  - **Tier 1 (High Impact)**: Results, Management Changes, M&A, Delisting, Fund Raise, Fraud/Litigation, Defaults, Credit Rating downgrades $\rightarrow$ Base 40–50 points.
  - **Tier 2 (Medium Impact)**: Dividends, Investor Meets, Credit Rating confirmations, Capex disclosures $\rightarrow$ Base 20–30 points.
  - **Tier 3 (Operational / Low Impact)**: Trading window closures, press releases, secretarial filings $\rightarrow$ Base 5–10 points.
- **Portfolio Weight Boost**:
  - Mock institutional portfolio weights (e.g., RELIANCE 12%, DIXON 8%, CDSL 5%, SUNPHARMA 6%).
  - Adds up to +25 points proportional to fund exposure.
- **Market Reaction Multiplier**:
  - Multiplier $\ge 1.4\times$ fires if the filing is accompanied by:
    - Stock price move $\ge 3.0\%$ on the filing date, OR
    - Daily trading volume $\ge 2.0\times$ the prior 20-session baseline average.
- **Timestamp Priority**:
  - Multi-filing events take the timestamp of the latest filing in the cluster, ranking high-momentum results (like RELIANCE and DIXON) at the top of the 72h window.

---

## 5. Model Routing & Token Cost Tracking

All model invocations are tracked in `pipeline/logs/cost_log.json` with input, output, and thinking tokens logged separately:

| Component / Stage | Model Routed | Prompt Strategy | Tokens (In / Out / Think) | Est. Cost (USD) |
|---|---|---|---|---|
| Stage 1: DIXON Guidance | `gemini-3.5-flash-lite` | Minimal thinking, JSON schema | 138,355 / 10,484 / 0 | $0.01352 |
| Stage 2: Q2 Results & Mgmt | Rules/Regex + Flash Lite | Structured table mapping | 94,133 / 13,238 / 0 | $0.00551 |
| Stage 4: DIXON Annual Report | Rules / PyMuPDF regex | Verified page extraction | 0 / 0 / 0 | $0.00000 |
| Stage 5: DIXON Synthesis | `gemini-3-flash-preview` | Feed restricted to 42 fact IDs | 2,841 / 1,898 / 0 | $0.00041 |
| KAYNES Concalls & Synthesis | `gemini-3.5-flash-lite` | Zero thinking, fact audit | 21,549 / 2,019 / 0 | $0.00109 |
| M&M Concall Pipeline | `gemini-3.5-flash-lite` | Minimal thinking extraction | 32,086 / 884 / 0 | $0.00135 |
| ASTRAL Concall Pipeline | `gemini-3.5-flash-lite` | Minimal thinking extraction | 14,612 / 1,966 / 0 | $0.00084 |
| INFY Concall Pipeline | `gemini-3.5-flash-lite` | Minimal thinking extraction | 11,076 / 802 / 0 | $0.00057 |
| PIDILITIND Concall Pipeline | `gemini-3.5-flash-lite` | Minimal thinking extraction | 6,711 / 5 / 0 | $0.00027 |
| HCLTECH Concall Pipeline | `gemini-3.5-flash-lite` | Minimal thinking extraction | 15,882 / 3,040 / 0 | $0.00105 |
| **Total Pipeline Operations** | — | — | **376,330 total tokens** | **$0.02535 USD** |

*Note: Free-tier routing routes high-volume extraction to `gemini-3.5-flash-lite` (zero thinking) and synthesis to `gemini-3-flash-preview` (strongest model with active quota) to ensure zero 429 quota failures.*

---

## 6. Local Setup & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Valid `GEMINI_API_KEY` in root `.env`

### 1. Python Environment Setup
```powershell
# Install pinned dependencies
pip install -r requirements.txt

# Run startup environment check
python -m pipeline.test_gemini_startup
```

### 2. Run Python Pipelines
```powershell
# Run full research pipeline for any ticker
python -m pipeline.research --ticker DIXON
python -m pipeline.research --ticker KAYNES

# Run stage 4 annual report extractor
python -m pipeline.extract_stage4

# Run stage 5 facts synthesis
python -m pipeline.synthesize_stage5
```

### 3. Start Backend API
```powershell
uvicorn pipeline.api:app --host 127.0.0.1 --port 8000 --reload
```
API endpoints available:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/research/DIXON`

### 4. Start React Frontend
```powershell
cd web
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

To verify a production build:
```powershell
npm run build --prefix web
```

---

## 7. Deliberately Omitted Items & Engineering Trade-Offs

To maintain zero-compromise institutional data integrity, the following features were deliberately scoped out of this challenge phase:
1. **Voice / Audio Generation**: Audio podcast generation from filings was omitted to prioritize 100% mathematical precision and primary citation verification.
2. **Native Mobile Push Notifications**: Simulated in UI with client-side localStorage alert banners rather than integrating APNS/FCM keys.
3. **LinkedIn / Social Media Profiles**: Scraped LinkedIn executive bios were omitted because unauthenticated scraping hallucinates executive identities; profiles are drawn exclusively from primary appointment PDFs.
4. **Cloud IP Bypass Solutions**: Cloud-based crawlers (e.g., AWS/Render) are blocked by NSE/Screener anti-bot firewalls. Rather than using brittle proxy meshes that violate securities platform terms, FINN uses an institutional **snapshot-first architecture** with graceful fallback to cached dossiers in demo environments.

---

## 8. Verification Checklist for Reviewer

Reviewers can verify all primary claims and code integrity by hand:
- [x] **Zero Hardcoded Numbers**: All financials come from `results.json` and primary PDFs.
- [x] **Zero Committed Secrets**: Run `git grep -n API_KEY` to confirm zero committed API keys.
- [x] **Strict Substring Audit**: Run `python -m pipeline.research --ticker DIXON` and verify that all 13 quotes match document text.
- [x] **Dixon QoQ Reconciliation**: Jul 2026 revenue of ₹21,862.37 Cr vs Q1 ₹16,075.95 Cr yields +36.0% QoQ (results.json, p.11).
- [x] **Cash Flow Conversion**: Dixon FY26 CFO ₹1,782 Cr vs PAT ₹1,644 Cr (108.4% conversion) verified on Annual Report p.420.
- [x] **Kaynes Negative CFO**: Kaynes FY26 CFO of -₹600.4 Cr verified on Annual Report p.240.
- [x] **Clean Production Build**: Run `npm run build --prefix web` (builds in ~3.0s with 0 errors).
- [x] **Git Cleanliness**: All 9 challenge stages committed sequentially to `main` with detailed progress logs.

