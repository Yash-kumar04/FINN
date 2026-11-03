"""
pipeline/cost_tracker.py
Centralized cost and token usage logger for FINN pipeline stages.
Saves input, output, and thinking tokens to pipeline/logs/cost_log.json.
"""

import os
import json
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")
COST_LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "cost_log.json")

# Rates per 1M tokens in USD
PRICING = {
    "gemini-3.5-flash": {"input": 0.075, "output": 0.30, "thinking": 0.30},
    "gemini-3.5-flash-lite": {"input": 0.0375, "output": 0.15, "thinking": 0.15},
    "gemini-3.1-pro-preview": {"input": 1.25, "output": 5.00, "thinking": 5.00},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00, "thinking": 5.00},
    "default": {"input": 0.075, "output": 0.30, "thinking": 0.30}
}


def log_cost(stage: str, model: str, input_tokens: int, output_tokens: int, thinking_tokens: int = 0, notes: str = ""):
    os.makedirs(os.path.dirname(COST_LOG_FILE), exist_ok=True)
    
    data = {
        "summary": {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_thinking_tokens": 0,
            "total_tokens": 0,
            "total_estimated_cost_usd": 0.0
        },
        "entries": []
    }
    
    if os.path.exists(COST_LOG_FILE):
        try:
            with open(COST_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    rates = PRICING.get(model, PRICING["default"])
    cost_usd = (
        (input_tokens / 1_000_000) * rates["input"] +
        (output_tokens / 1_000_000) * rates["output"] +
        (thinking_tokens / 1_000_000) * rates["thinking"]
    )

    entry = {
        "timestamp_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
        "stage": stage,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "thinking_tokens": thinking_tokens,
        "total_tokens": input_tokens + output_tokens + thinking_tokens,
        "estimated_cost_usd": round(cost_usd, 6),
        "notes": notes
    }
    
    data["entries"].append(entry)
    
    # Recalculate summary
    tot_in = sum(e["input_tokens"] for e in data["entries"])
    tot_out = sum(e["output_tokens"] for e in data["entries"])
    tot_think = sum(e["thinking_tokens"] for e in data["entries"])
    tot_cost = sum(e["estimated_cost_usd"] for e in data["entries"])
    
    data["summary"] = {
        "total_input_tokens": tot_in,
        "total_output_tokens": tot_out,
        "total_thinking_tokens": tot_think,
        "total_tokens": tot_in + tot_out + tot_think,
        "total_estimated_cost_usd": round(tot_cost, 6)
    }

    with open(COST_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return entry

