"""
pipeline/fetch_prices.py
Fetches 60 trading days of raw daily OHLCV for all 19 portfolio tickers from yfinance.

Rules:
- Never round, never estimate.
- Ensure the latest completed trading session (2026-11-02) is included.
- Mark latest bar 'provisional' ONLY if fetched while that session is still open.
- Record provenance: source, fetched_at_ist, as_of_date.
- If source fails, record status: "source_unavailable"; never drop the ticker.
- Writes to web/public/data/prices.json
"""

import os
import sys

# Ensure UTF-8 output on Windows PowerShell
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import math
from datetime import datetime
import pytz
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()
IST = pytz.timezone("Asia/Kolkata")

PORTFOLIO = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy / Retail / Telecom", "cap": "Mega", "weight": 0.12},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Capital Goods / Infrastructure", "cap": "Large", "weight": 0.08},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking / Financials", "cap": "Mega", "weight": 0.10},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking / Financials", "cap": "Large", "weight": 0.08},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "Banking / Financials", "cap": "Large", "weight": 0.05},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "IT Services", "cap": "Mega", "weight": 0.08},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT Services", "cap": "Large", "weight": 0.06},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki India", "sector": "Automobile (Passenger)", "cap": "Large", "weight": 0.05},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra", "sector": "Automobile (SUV/EV/Agri)", "cap": "Large", "weight": 0.05},
    {"symbol": "BAJAJ-AUTO.NS", "name": "Bajaj Auto", "sector": "Automobile (2W/3W/EV)", "cap": "Large", "weight": 0.04},
    {"symbol": "DIXON.NS", "name": "Dixon Technologies", "sector": "Electronics Manufacturing (EMS)", "cap": "Mid", "weight": 0.04},
    {"symbol": "KAYNES.NS", "name": "Kaynes Technology", "sector": "Electronics Manufacturing / IoT", "cap": "Small/Mid", "weight": 0.03},
    {"symbol": "POLYCAB.NS", "name": "Polycab India", "sector": "Cables & Fast Moving Electricals", "cap": "Large", "weight": 0.04},
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics", "sector": "Aerospace & Defence", "cap": "Large", "weight": 0.04},
    {"symbol": "BEL.NS", "name": "Bharat Electronics", "sector": "Defence Electronics", "cap": "Large", "weight": 0.04},
    {"symbol": "TRENT.NS", "name": "Trent Ltd", "sector": "Retail / Consumer", "cap": "Large", "weight": 0.05},
    {"symbol": "TITAN.NS", "name": "Titan Company", "sector": "Consumer Discretionary / Luxury", "cap": "Large", "weight": 0.04},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharma Industries", "sector": "Pharma & Healthcare", "cap": "Large", "weight": 0.04},
    {"symbol": "CDSL.NS", "name": "Central Depository Services", "sector": "Capital Market Infrastructure", "cap": "Mid", "weight": 0.02},
]

TARGET_BAR_COUNT = 60

def is_bar_provisional(fetched_at_ist: datetime, bar_date_str: str) -> bool:
    """
    Mark latest bar provisional ONLY if fetched while that market session is still open.
    Indian equity trading hours: 09:15 to 15:30 IST on weekdays.
    If bar_date is a past completed day, it is never provisional.
    """
    today_str = fetched_at_ist.strftime("%Y-%m-%d")
    is_today = (bar_date_str == today_str)
    is_weekday = (fetched_at_ist.weekday() < 5)
    
    current_time_minutes = fetched_at_ist.hour * 60 + fetched_at_ist.minute
    market_open = 9 * 60 + 15
    market_close = 15 * 60 + 30
    
    session_open = (market_open <= current_time_minutes <= market_close)
    return is_today and is_weekday and session_open


def fetch_all_prices():
    now_ist = datetime.now(IST)
    fetched_at_str = now_ist.isoformat()

    results = {}
    print(f"Fetching 60-day raw OHLCV for {len(PORTFOLIO)} portfolio tickers at {fetched_at_str}...")

    for item in PORTFOLIO:
        sym = item["symbol"]
        print(f"  Fetching {sym:<16}...", end=" ", flush=True)

        try:
            t = yf.Ticker(sym)
            hist = t.history(period="4mo", auto_adjust=False)

            if hist.empty or len(hist) < 5:
                print("❌ EMPTY / INSUFFICIENT DATA")
                results[sym] = {
                    "symbol": sym,
                    "name": item["name"],
                    "sector": item["sector"],
                    "cap": item["cap"],
                    "portfolio_weight": item["weight"],
                    "status": "source_unavailable",
                    "error": "yfinance returned empty or insufficient historical data",
                    "provenance": {
                        "source": "yfinance",
                        "fetched_at_ist": fetched_at_str,
                        "as_of_date": None
                    },
                    "bars": []
                }
                continue

            # Check if last row is Nov 2 with NaN Close due to midnight rollover reconciliation
            last_idx = hist.index[-1]
            last_row = hist.iloc[-1]
            
            if math.isnan(last_row["Close"]):
                # Reconcile from fast_info if fast_info has completed session data
                try:
                    fi = t.fast_info
                    if fi and fi.last_price is not None and not math.isnan(fi.last_price):
                        hist.loc[last_idx, "Open"] = float(fi.open) if fi.open is not None else float(last_row["Open"])
                        hist.loc[last_idx, "High"] = float(fi.day_high) if fi.day_high is not None else float(last_row["High"])
                        hist.loc[last_idx, "Low"] = float(fi.day_low) if fi.day_low is not None else float(last_row["Low"])
                        hist.loc[last_idx, "Close"] = float(fi.last_price)
                        if "Adj Close" in hist.columns:
                            hist.loc[last_idx, "Adj Close"] = float(fi.last_price)
                        if fi.last_volume is not None:
                            hist.loc[last_idx, "Volume"] = int(fi.last_volume)
                except Exception as ex:
                    print(f"[fast_info note for {sym}: {ex}]", end=" ")

            # Clean any remaining NaNs
            hist = hist.dropna(subset=["Close"])

            # Take the last 60 trading days
            hist_60 = hist.tail(TARGET_BAR_COUNT)
            bars = []

            for idx, row in hist_60.iterrows():
                bar_date = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                bars.append({
                    "date": bar_date,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "adj_close": float(row["Adj Close"]) if "Adj Close" in row else float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "provisional": False
                })

            # Check if last bar is provisional
            last_bar = bars[-1]
            if is_bar_provisional(now_ist, last_bar["date"]):
                last_bar["provisional"] = True

            as_of_date = last_bar["date"]

            # Calculate 20-day moving average volume (PRIOR 20 sessions, excluding the latest bar)
            vol_20d = [b["volume"] for b in bars[-21:-1]]
            avg_vol_20d = sum(vol_20d) / len(vol_20d) if vol_20d else last_bar["volume"]

            # Calculate 1-day price and volume changes
            if len(bars) >= 2:
                prev_bar = bars[-2]
                price_change_pct = ((last_bar["close"] - prev_bar["close"]) / prev_bar["close"]) * 100.0
                volume_ratio = (last_bar["volume"] / avg_vol_20d) if avg_vol_20d > 0 else 1.0
            else:
                price_change_pct = 0.0
                volume_ratio = 1.0

            results[sym] = {
                "symbol": sym,
                "name": item["name"],
                "sector": item["sector"],
                "cap": item["cap"],
                "portfolio_weight": item["weight"],
                "status": "ok",
                "provenance": {
                    "source": "yfinance",
                    "fetched_at_ist": fetched_at_str,
                    "as_of_date": as_of_date
                },
                "metrics": {
                    "last_close": last_bar["close"],
                    "last_volume": last_bar["volume"],
                    "prev_close": bars[-2]["close"] if len(bars) >= 2 else last_bar["close"],
                    "price_change_pct": price_change_pct,
                    "volume_20d_avg": avg_vol_20d,
                    "volume_ratio": volume_ratio,
                    "is_provisional": last_bar["provisional"]
                },
                "bar_count": len(bars),
                "bars": bars
            }
            print(f"✅ OK ({len(bars)} bars, as_of={as_of_date}, close={last_bar['close']}, chg={price_change_pct:+.2f}%)")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results[sym] = {
                "symbol": sym,
                "name": item["name"],
                "sector": item["sector"],
                "cap": item["cap"],
                "portfolio_weight": item["weight"],
                "status": "source_unavailable",
                "error": str(e),
                "provenance": {
                    "source": "yfinance",
                    "fetched_at_ist": fetched_at_str,
                    "as_of_date": None
                },
                "bars": []
            }

    snapshot = {
        "dataset": "portfolio_prices",
        "provenance": {
            "source": "yfinance",
            "fetched_at_ist": fetched_at_str,
            "as_of_date": max(v["provenance"]["as_of_date"] for v in results.values() if v.get("provenance", {}).get("as_of_date")),
            "target_bar_count": TARGET_BAR_COUNT,
            "portfolio_size": len(PORTFOLIO)
        },
        "summary": {
            "total_tickers": len(PORTFOLIO),
            "ok_count": sum(1 for v in results.values() if v["status"] == "ok"),
            "unavailable_count": sum(1 for v in results.values() if v["status"] == "source_unavailable")
        },
        "tickers": results
    }

    out_file = "web/public/data/prices.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    print(f"\nSaved raw unrounded price snapshot with Nov 2 bar to {out_file}")
    return snapshot

if __name__ == "__main__":
    fetch_all_prices()
