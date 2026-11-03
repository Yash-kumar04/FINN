build-history/README.md

# Build history: Antigravity (coding agent) logs

Files are raw, unedited conversations. Order of work:

1. Planning: read the brief, wrote SPEC.md and PLAN.md
2. Data-source probes: yfinance, NSE announcements, screener.in, Gemini model list
3. Pipeline: prices, announcements, rules-based classifier, event grouping
4. Fixes found in review: partial-day price bar, volume baseline, ranking
5. Briefing UI and configurable alerts
6. Results cards and management cards (with validation)
7. Research engine: guidance, verdicts, annual-report facts, bull/bear
8. Backend (FastAPI on Render), README, final fixes

I reviewed the agent's output in a separate Claude chat, which is not included.
Stage-by-stage verification output is in PROGRESS.md and pipeline/logs/.