# PLAN: FINN Prototype Build Plan (1-Page)

## 1. Core Architecture Strategy: Snapshot-First
To guarantee a zero-fail, sub-second demo on deadline day, we strictly decouple **Data Ingestion** from **Client Presentation**:
- **Pipeline (`pipeline/`)**: Python CLI that fetches market data, parses primary filings, prompts Gemini for structured extraction, and writes static JSON to `src/data/`.
- **Frontend (`web/` or root React app)**: Mobile-first React + Vite app that reads local JSON by default. Zero dependency on live network/scrapers during the demo, with an optional toggle to run the live backend for ad-hoc tickers.

---

## 2. The Cut List (Deliberate Non-Essentials)
To ensure a flawless deliverable today, the following are explicitly cut:
- **Cut**: Real-time websocket price tickers (EOD closes are standard for fundamental daily digests).
- **Cut**: User authentication / cloud database (mock portfolio in state / localStorage).
- **Cut**: In-app full PDF rendering (replaced by interactive citation cards showing verbatim excerpts and page numbers).
- **Cut**: Voice interface / audio generation.
- **Cut**: Live scraping directly from the browser on page load (fragile and rate-limited).

---

## 3. Build Order & Progressive Checkpoints

| Step | Scope | Deliverable | Checkpoint (Definition of Done) |
| :--- | :--- | :--- | :--- |
| **0. Test Probes** | Validate data sources | Quick 15-line test scripts for yfinance, NSE/BSE announcements, Screener HTML, and Gemini API. | Probes execute successfully without HTTP 403 or schema errors. |
| **1. Data Contracts & Snapshots** | Build schemas & pre-baked JSON | `portfolio_briefing.json` (16 stocks, tiered filings, results cards, C-suite changes) and `research/{TICKER}.json` (Dixon, Trent, Kaynes, Tata Motors). | JSON files pass structural schema validation; sample cards render valid numbers. |
| **2. Mobile App Shell** | Setup React + Vite + Tailwind | Mobile viewport frame (390px default, responsive), bottom navigation (`Briefing` vs `Research`), and status pill. | `npm run build && npm run preview` works cleanly on mobile browser viewport. |
| **3. Push Feed (Briefing Tab)** | Implement ranking, cards, & alerts | Time-window picker (24h/3D/7D/30D), threshold sliders (Price $\pm X\%$, Volume $>K\times$), Results card with QoQ/YoY deltas, Management dossier, and collapsed routine filings bar. | Changing slider filters feed dynamically; tapping collapsed bar expands 15+ routine filings; Results card shows clear green/red margin pills. |
| **4. Pull View (Research Tab)** | Implement Hero Matrix & Citations | Ticker picker, **Promised vs Delivered** 4-quarter matrix, Cash Quality chart (CFO vs PAT), Bull/Bear cards, and interactive citation popovers. | Clicking `[Q2 FY25 Concall, p. 14]` pops open verbatim quote; Promised vs Delivered shows clear Met/Missed/Beat verdicts. |
| **5. Generalisation Engine** | Ad-hoc CLI / API runner | `python -m pipeline.run_research --ticker <SYMBOL>`: fetches Screener data, invokes Gemini 2.5/1.5 Flash with structured output schema, outputs new JSON to `src/data/research/`. | Running CLI for a new ticker (e.g. `INFY`) generates a valid, viewable research dossier. |
| **6. Packaging & Cover Note** | Final review & export | Production build verification, README with deployment/run instructions, and assessment covering email draft. | App runs locally with 1 command (`npm run dev`); mobile preview passes audit; AI build logs organized. |

---

## 4. Top Uncertainties & Risk Test Strategy

1. **NSE Anti-Bot Blocking & Session Cookies**:
   - *Risk*: `nseindia.com` blocks direct requests with Cloudflare / 403 Forbidden.
   - *Test First*: Run test script probing BSE Announcements API (`api.bseindia.com`) vs NSE with browser headers.
   - *Mitigation*: BSE provides cleaner, less aggressive JSON endpoints for announcements. Pre-baked snapshots guarantee demo integrity regardless.
2. **Screener.in Transcript Availability & External Hosting**:
   - *Risk*: Concall transcripts on Screener link out to external third-party PDFs or vary in format.
   - *Test First*: Probe Screener's HTML structure for 3 tickers (`DIXON`, `TRENT`, `TATAMOTORS`) to extract transcript URLs and quarterly tables.
   - *Mitigation*: Screener's consolidated quarterly tables provide direct structured data; transcripts are pre-downloaded and chunked for core demo tickers.
3. **Gemini Context & Extraction Latency**:
   - *Risk*: Feeding 30-page concalls into an LLM repeatedly is slow and exceeds rate limits.
   - *Test First*: Extract Management Remarks and Q&A sections first using regex/heuristics, then run structured schema extraction using `gemini-2.5-flash` or `gemini-1.5-flash`.
   - *Mitigation*: Snapshot-first architecture removes all live LLM dependencies during user evaluation.

---

## 5. Open Questions for Product Alignment
1. **Portfolio Presets**: For the 16–20 mock portfolio, do you have specific preferred companies beyond our proposed mix (Dixon, Trent, Kaynes, Tata Motors, Reliance, TCS, HDFC Bank, CDSL, HAL, Zomato, etc.)?
2. **Deployment Preference**: For the mobile demo deliverable, is a Vercel/Netlify live link preferred, or a clean local Vite server with instructions (or both)?
3. **Ad-hoc Pull Mode in UI**: Should the research search bar trigger the local Python backend dynamically via a lightweight local endpoint, or is a CLI command (`python -m pipeline.run_research --ticker XYZ`) sufficient for proving generalization?

