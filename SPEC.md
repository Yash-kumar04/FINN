# SPEC: FINN — Financial Investment Agent

## 1. Product Mission & Philosophy

**FINN** is a mobile-first, high-conviction financial intelligence agent designed for public-markets investors managing Indian equities (NSE/BSE). 

Public market investors do not suffer from a lack of data; they are overwhelmed by noise. Every day brings hundreds of exchange filings, secretarial certificates, market rumors, and price fluctuations. The scarce capability is **selective filtering**: aggressively burying routine compliance paperwork while immediately surfacing, contextualizing, and analyzing the 2% of disclosures that move intrinsic business value.

FINN operates in two complementary interaction modes:
1. **Push (Morning Briefing / Pulse)**: An intelligent, windowed feed that surfaces high-conviction portfolio events (results with margin deltas, C-suite changes with executive dossiers, unusual volume/price breakouts) while collapsing routine compliance filings into single-line aggregates.
2. **Pull (Deep-Dive Research Engine)**: On-demand fundamental equity analysis for any NSE ticker, strictly grounded in primary sources (Annual Reports and Earnings Call Transcripts), anchored by a flagship **"Promised vs. Delivered"** accountability matrix.

---

## 2. Evaluation Criteria & Grading Signals (Our Interpretation)

Based on the ENAM challenge brief, success is measured along five explicit signals:

| Grading Signal | What Evaluators Care About | What We Must Avoid (Anti-Patterns) |
| :--- | :--- | :--- |
| **Product Sense & Signal Filtering** | High information density, beautiful mobile interaction, intelligent curation. Pushing what an investor *must* know and burying what they don't. | Dumping raw feeds, unranked lists, missing business context, clunky desktop layouts on mobile. |
| **Grounding Discipline ("No AI Slop")** | Strict, verifiable grounding in primary company disclosures (Annual Reports + Concall Transcripts). Verifiable quotes and line/page citations. | Hallucinating numbers, citing third-party broker opinions/news, generic LLM fluff without primary data attribution. |
| **Hero Analytical Depth (Promised vs. Delivered)** | Differentiating *analysis* from *summarization*. Tracking multi-quarter management guidance against realized financials to assess executive credibility. | Superficial bullet points that merely rehash management commentary without holding them accountable to past claims. |
| **Architectural Judgment & Demo Reliability** | **Snapshot-first architecture**: pre-computed JSON snapshots guarantee the demo never fails, lags, or crashes due to rate limits. Clean generalization pipeline for ad-hoc tickers. | "Broad but broken" demo; relying on live web-scraping during an evaluation; fragile blocking network calls. |
| **Cost & Token Efficiency** | Smart model routing (fast/cheap models for structured extraction, reasoning models for synthesis), prompt caching, and concise representations. | Unbounded multi-megabyte PDF dumping into LLM context windows; wasteful multi-agent loops. |

---

## 3. Product Architecture & User Experience

### 3.1 Interaction Model: Mobile-First Responsive Web
- **Format**: Responsive web app optimized for mobile viewports (375px–430px width: iPhone/Android standard) while scaling cleanly to desktop.
- **Navigation**: Persistent bottom tab bar with two primary views:
  1. `Briefing` (Push Feed)
  2. `Research` (Pull Analysis)
- **Top Header**: Portfolio switcher / Status indicator (`Offline Snapshot Mode` vs `Live Pipeline`).

---

## 4. Feature Specifications

### 4.1 Push Mode: The Portfolio Briefing (Push Feed)

#### Portfolio Scope
- **Universe**: Mock portfolio of 16-20 diverse NSE companies spanning large, mid, and small-caps across sectors (e.g., Reliance, TCS, HDFC Bank, Tata Motors, Dixon Technologies, Trent, Kaynes Tech, CDSL, HAL, Zomato, Polycab, Cipla, Deepak Nitrite, Suzlon).

#### Capabilities
1. **Windowed Digest**:
   - Time window selector: `Last 24 Hours` (default), `3 Days`, `7 Days`, `30 Days`.
   - Filters filings based on timestamp and significance.
2. **Signal Classification & Ranking Hierarchy**:
   - **Tier 1 (High Priority / Actionable)**: `results`, `management_change`, `M&A`, `fund_raise`, `litigation`, `capex`. Surfaced at the top as expanded rich cards.
   - **Tier 2 (Informational)**: `credit_rating`, `dividend`, `bonus_split`, `insider_trading`, `press_release`. Compact cards with 1-line key takeaway.
   - **Tier 3 (Routine Paperwork)**: `postal_ballot`, `agm_egm`, `pledging`, `unclassified` (ESOPs, compliance certificates, secretarial filings). Collapsed into an expandable aggregate bar (e.g., *"18 routine filings collapsed — tap to view"*).
3. **Configurable Alert Thresholds**:
   - **Price Move Slider**: Trigger alert when absolute 1-day change exceeds $\pm X\%$ (default: $\pm 3\%$, adjustable from $1\%$ to $10\%$).
   - **Volume Spike Slider**: Trigger alert when traded volume exceeds $K \times$ 20-day moving average (default: $2.0\times$, adjustable from $1.5\times$ to $5.0\times$).
   - Matched items display visual warning badges (`🔥 3.2x Vol Spike`, `🔻 -4.8% Price Drop`).
4. **Rich Card Designs**:
   - **Quarterly Results Card**:
     - Headline Metrics Grid: **Revenue**, **EBITDA**, **PBT**, **PAT**.
     - Deltas: Quarter-on-Quarter (QoQ) and Year-on-Year (YoY) with colored trend pills.
     - Profitability: EBITDA margin and margin expansion/contraction.
     - Analytical Takeaway: 1-2 sentence core driver (e.g., *"Revenue up 18% YoY driven by mobile segment, but EBITDA margin contracted 120 bps due to raw material inflation."*).
   - **Management Change Card**:
     - Executive Dossier: Outgoing vs. Incoming role holder.
     - Background & Pedigree: Short bio (past companies, tenure, credentials).
     - Strategic Signal: Brief assessment of why this transition matters to investors.

---

### 4.2 Pull Mode: The On-Demand Research Engine

#### Universe & Generalization
- Pre-baked deep research dossiers for key demo tickers (e.g., `DIXON`, `TRENT`, `KAYNES`, `TATAMOTORS`).
- On-demand research runner capable of generating dossiers for any NSE ticker given accessible transcripts and annual reports.

#### Core Analysis Modules
1. **Hero Feature: Promised vs. Delivered (Accountability Matrix)**:
   - 4-quarter chronological scorecard tracking management guidance vs. actual outcomes.
   - Columns: `Quarter Guided`, `Management Promise / Commentary`, `Target Quarter`, `Delivered Number / Reality`, `Verdict` (`Beat`, `Met`, `Missed`, `Pivoted`).
   - Every cell anchors to an exact, clickable primary quote with document attribution.
2. **Verifiable Primary-Source Grounding**:
   - No generic claims. Every factual point carries a clickable citation chip: e.g., `[Q2 FY25 Concall, p. 14]` or `[AR FY24, p. 72]`.
   - Clicking a citation displays the exact verbatim excerpt in a drawer or popover.
3. **Core Fundamental Modules**:
   - **Business & Revenue Snapshot**: Business model, operating segments, and revenue mix.
   - **Financial Trajectory**: Multi-year growth trends, operating margins, ROCE/ROE, working capital cycle, and leverage ($D/E$).
   - **Cash Quality Audit**: Operating Cash Flow (CFO) vs. PAT cash conversion ratio over 3 years. Flags whether accounting profits translate to real cash.
   - **Bull vs. Bear Synthesis**: A sharp 3-point Bull Case vs. 3-point Bear Case, constructed entirely from capacity/demand dynamics, competitive commentary, and disclosures.
4. **Interactive Primary-Grounded Q&A (Copilot)**:
   - Investor can type a specific inquiry (e.g., *"What is management's target for EMS export margins in FY26?"*).
   - Engine answers concisely using only primary source context, with direct citations.

---

## 5. Technical Architecture & Data Ingestion Strategy

```
┌────────────────────────────────────────────────────────┐
│                   FINN Web Client                     │
│               (React + Vite + Tailwind)                │
│       Mobile-First UI • Zero-Latency Snapshot Reader   │
└───────────────────────────▲────────────────────────────┘
                            │ Reads static / API JSON
┌───────────────────────────┴────────────────────────────┐
│                  Data Snapshot Layer                   │
│             /data/portfolio_briefing.json              │
│             /data/research/{TICKER}.json               │
└───────────────────────────▲────────────────────────────┘
                            │ Generated / Updated by
┌───────────────────────────┴────────────────────────────┐
│                 Python Pipeline Engine                 │
│                                                        │
│  1. yfinance (EOD Price, Volume, 20-DMA)               │
│  2. Exchange Filings (NSE / BSE RSS & Announcements)   │
│  3. Screener Parser (Concall Transcripts & AR links)   │
│  4. Gemini 2.5 / 1.5 Flash (Structured Extraction)     │
└────────────────────────────────────────────────────────┘
```

1. **Snapshot-First Reliability**:
   - The React frontend ships with pre-compiled, rich JSON datasets under `src/data/`.
   - The app runs instantly and reliably in any environment without requiring active scrapers, backend processes, or external API keys during initial UI evaluation.
2. **Generalization Pipeline (`pipeline/`)**:
   - Modular Python scripts:
     - `fetch_market_data.py`: Fetches prices and volumes via `yfinance`.
     - `fetch_announcements.py`: Ingests and categorizes corporate announcements into the 17 taxonomy types.
     - `research_extractor.py`: Parses transcripts and annual reports, queries Gemini with structured schema prompts, and produces standardized research JSON.

---

## 6. Non-Functional & Operational Requirements
- **Target OS**: Windows, Python 3.13, Node.js.
- **Zero API Key Leakage**: `GEMINI_API_KEY` stored exclusively in `.env`; backend scripts access it via `os.environ`; client build never bundles keys.
- **Portability**: Production build (`npm run build`) outputs static HTML/JS/CSS deployable to Vercel, Netlify, or local preview in seconds.

