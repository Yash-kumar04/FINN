"""
pipeline/api.py
FastAPI backend for FINN Financial Intelligence platform.

Endpoints:
- GET /health -> {"status": "ok"}
- GET /api/health -> {"status": "ok"}
- GET /research/{ticker} & GET /api/research/{ticker}
  * Validates ticker format with ^[A-Z0-9&-]{1,20}$
  * Cached tickers are always served immediately (no job limits applied).
  * Rate limits:
    - Only 1 live pipeline job running at any time.
    - At most 10 live pipeline jobs per day (tracked in IST).
  * Returns {"status": "unavailable", "reason": ...} when over limits or blocked.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import re
import json
import threading
from datetime import datetime
import pytz
from typing import Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

IST = pytz.timezone("Asia/Kolkata")
TICKER_REGEX = re.compile(r"^[A-Z0-9&-]{1,20}$")
MAX_JOBS_PER_DAY = 10

app = FastAPI(title="FINN Financial Intelligence API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESEARCH_DIR = os.path.join("web", "public", "data", "research")

# Thread-safe rate limiter state
LOCK = threading.Lock()
ACTIVE_JOBS: Dict[str, Dict[str, Any]] = {}
CURRENT_LIVE_JOB: Optional[str] = None
DAILY_JOB_COUNT: int = 0
CURRENT_DAY_IST: str = datetime.now(IST).strftime("%Y-%m-%d")


def run_pipeline_for_ticker(ticker: str):
    """Background worker executing research extraction."""
    global CURRENT_LIVE_JOB
    clean_sym = ticker.strip().upper()
    try:
        from pipeline.research import fetch_screener_transcript_links, process_transcript, execute_part2
        links = fetch_screener_transcript_links(clean_sym, limit=5)
        if not links:
            with LOCK:
                ACTIVE_JOBS[clean_sym] = {
                    "status": "unavailable",
                    "reason": f"No earnings concall transcripts found on Screener for {clean_sym}."
                }
            return

        records = []
        for l in links:
            rec = process_transcript(l)
            records.append(rec)

        execute_part2(clean_sym, records)

        with LOCK:
            ACTIVE_JOBS[clean_sym] = {"status": "done"}
    except Exception as exc:
        with LOCK:
            ACTIVE_JOBS[clean_sym] = {
                "status": "unavailable",
                "reason": f"Primary data pipeline error: {str(exc)}"
            }
    finally:
        with LOCK:
            CURRENT_LIVE_JOB = None


@app.get("/")
def root():
    return {
        "service": "FINN Financial Intelligence API",
        "status": "running",
        "live_job_in_progress": CURRENT_LIVE_JOB,
        "daily_jobs_used": DAILY_JOB_COUNT,
        "daily_limit": MAX_JOBS_PER_DAY
    }


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/research/{ticker}")
@app.get("/api/research/{ticker}")
def get_research(ticker: str, background_tasks: BackgroundTasks):
    global CURRENT_LIVE_JOB, DAILY_JOB_COUNT, CURRENT_DAY_IST

    sym = ticker.strip().upper()

    # 1. Validate ticker format: ^[A-Z0-9&-]{1,20}$
    if not TICKER_REGEX.match(sym):
        return JSONResponse(
            status_code=400,
            content={
                "status": "unavailable",
                "reason": f"Invalid ticker '{ticker}'. Ticker must match regex ^[A-Z0-9&-]{{1,20}}$."
            }
        )

    cache_path = os.path.join(RESEARCH_DIR, f"{sym}.json")

    # 2. Rule: Cached tickers are ALWAYS served (bypass live job concurrency & daily limits)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content=data)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "unavailable", "reason": f"Corrupted cache file for {sym}: {e}"}
            )

    # 3. Check existing job status for this ticker
    with LOCK:
        today_str = datetime.now(IST).strftime("%Y-%m-%d")
        if today_str != CURRENT_DAY_IST:
            CURRENT_DAY_IST = today_str
            DAILY_JOB_COUNT = 0

        job = ACTIVE_JOBS.get(sym)
        if job:
            if job["status"] == "processing":
                return JSONResponse(
                    status_code=202,
                    content={
                        "status": "processing",
                        "ticker": sym,
                        "message": "Research pipeline is running in background"
                    }
                )
            elif job["status"] == "unavailable":
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unavailable",
                        "ticker": sym,
                        "reason": job.get("reason", "Pipeline blocked")
                    }
                )
            elif job["status"] == "done":
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        return JSONResponse(content=json.load(f))

        # 4. Concurrency Limit: Allow only ONE live job at a time
        if CURRENT_LIVE_JOB is not None:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "unavailable",
                    "reason": f"Another live research job is currently running ({CURRENT_LIVE_JOB}). Only one live job is permitted at a time."
                }
            )

        # 5. Daily Limit: At most 10 live jobs per day
        if DAILY_JOB_COUNT >= MAX_JOBS_PER_DAY:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "unavailable",
                    "reason": f"Daily limit of {MAX_JOBS_PER_DAY} live research jobs exceeded for today ({CURRENT_DAY_IST}). Cached tickers remain available."
                }
            )

        # Reserve slot
        CURRENT_LIVE_JOB = sym
        DAILY_JOB_COUNT += 1
        ACTIVE_JOBS[sym] = {"status": "processing"}

    # Start background task
    background_tasks.add_task(run_pipeline_for_ticker, sym)

    return JSONResponse(
        status_code=202,
        content={
            "status": "processing",
            "ticker": sym,
            "jobs_today": DAILY_JOB_COUNT,
            "daily_limit": MAX_JOBS_PER_DAY,
            "message": "Triggered background pipeline job"
        }
    )
