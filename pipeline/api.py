"""
pipeline/api.py
FastAPI backend for FINN Financial Intelligence platform.
Endpoints:
- GET /health -> {"status": "ok"}
- GET /api/health -> {"status": "ok"}
- GET /research/{ticker} & GET /api/research/{ticker}
  * Returns cached research dossier from web/public/data/research/{ticker}.json if present.
  * If absent, kicks off background pipeline thread and returns {"status": "processing"}.
  * If blocked or failed, returns {"status": "unavailable", "reason": "<error>"}.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import json
import threading
from typing import Dict, Any
from fastapi import FastAPI, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="FINN Financial Intelligence API", version="1.0.0")

# Enable CORS for localhost and Vercel domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESEARCH_DIR = os.path.join("web", "public", "data", "research")
ACTIVE_JOBS: Dict[str, Dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()


def run_pipeline_for_ticker(ticker: str):
    """Worker function executed in background thread."""
    clean_sym = ticker.strip().upper()
    try:
        from pipeline.research import fetch_screener_transcript_links, process_transcript, execute_part2
        links = fetch_screener_transcript_links(clean_sym, limit=5)
        if not links:
            with JOBS_LOCK:
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

        with JOBS_LOCK:
            ACTIVE_JOBS[clean_sym] = {"status": "done"}
    except Exception as exc:
        with JOBS_LOCK:
            ACTIVE_JOBS[clean_sym] = {
                "status": "unavailable",
                "reason": f"Primary data pipeline error: {str(exc)}"
            }


@app.get("/")
def root():
    return {"service": "FINN Financial Intelligence API", "status": "running"}


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/research/{ticker}")
@app.get("/api/research/{ticker}")
def get_research(ticker: str, background_tasks: BackgroundTasks):
    sym = ticker.strip().upper()
    cache_path = os.path.join(RESEARCH_DIR, f"{sym}.json")

    # 1. Return cached dossier if already generated
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content=data)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "reason": f"Corrupted cache file for {sym}: {e}"}
            )

    # 2. Check active background job status
    with JOBS_LOCK:
        job = ACTIVE_JOBS.get(sym)

    if job:
        if job["status"] == "processing":
            return JSONResponse(
                status_code=202,
                content={"status": "processing", "ticker": sym, "message": "Research pipeline is running in background"}
            )
        elif job["status"] == "unavailable":
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "ticker": sym, "reason": job.get("reason", "Pipeline blocked")}
            )
        elif job["status"] == "done":
            # Just finished; read now
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    return JSONResponse(content=json.load(f))

    # 3. Not cached and not running: start background job
    with JOBS_LOCK:
        ACTIVE_JOBS[sym] = {"status": "processing"}

    background_tasks.add_task(run_pipeline_for_ticker, sym)

    return JSONResponse(
        status_code=202,
        content={"status": "processing", "ticker": sym, "message": "Triggered background pipeline job"}
    )
