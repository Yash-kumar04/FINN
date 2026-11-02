"""
Investigate yfinance:
1. Print last 5 rows of raw yfinance data for RELIANCE.NS, HDFCBANK.NS, DIXON.NS, HAL.NS, TRENT.NS
2. Check last close dates, analyze the price data structure (round numbers, % changes)
3. Test ticker symbols for Tata Motors and Zomato (now Eternal)
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
import pandas as pd
import yfinance as yf

output_dir = "pipeline/probe_output"
os.makedirs(output_dir, exist_ok=True)

tickers_5 = ["RELIANCE.NS", "HDFCBANK.NS", "DIXON.NS", "HAL.NS", "TRENT.NS"]
raw_5_output = []

print("=" * 80)
print("1. RAW YFINANCE DATA FOR 5 TICKERS (LAST 5 ROWS)")
print("=" * 80)

for sym in tickers_5:
    t = yf.Ticker(sym)
    hist = t.history(period="1mo")
    print(f"\n>>> TICKER: {sym}")
    print(f"Data shape: {hist.shape}")
    print(f"Date index type: {type(hist.index)}")
    print(f"Last 5 rows:")
    last5 = hist.tail(5)
    print(last5[["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]])
    
    # Save raw to text
    raw_5_output.append(f"=== {sym} ===")
    raw_5_output.append(f"Last close date: {hist.index[-1]}")
    raw_5_output.append(last5.to_string())
    raw_5_output.append("\n")

with open(f"{output_dir}/yfinance_5tickers_raw.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(raw_5_output))

print(f"\nSaved raw 5-ticker history to {output_dir}/yfinance_5tickers_raw.txt")

# Test Tata Motors and Zomato/Eternal symbols
print("\n" + "=" * 80)
print("2. DIAGNOSTIC TESTING: TATA MOTORS AND ZOMATO / ETERNAL TICKERS")
print("=" * 80)

test_symbols = [
    # Tata Motors variants
    "TATAMOTORS.NS",
    "TATAMOTORS.BO",
    "500570.BO",       # BSE scrip code for Tata Motors
    "TATAMTRDVR.NS",
    "TATAMTRDVR.BO",
    "TMP.F",
    "TTM",
    # Zomato variants
    "ZOMATO.NS",
    "ZOMATO.BO",
    "543320.BO",       # BSE scrip code for Zomato
    "ETERNAL.NS",
    "ETERNAL.BO"
]

ticker_results = []
for s in test_symbols:
    try:
        t = yf.Ticker(s)
        h = t.history(period="5d")
        if not h.empty:
            last_date = str(h.index[-1].date())
            close = float(h["Close"].iloc[-1])
            vol = int(h["Volume"].iloc[-1])
            res = f"SUCCESS: {s} -> Last Date: {last_date}, Close: {close:.2f}, Volume: {vol:,}"
            ticker_results.append(res)
            print(f"✅ {res}")
        else:
            res = f"EMPTY: {s} -> Returned empty DataFrame"
            ticker_results.append(res)
            print(f"⚠️ {res}")
    except Exception as e:
        res = f"ERROR: {s} -> Exception: {e}"
        ticker_results.append(res)
        print(f"❌ {res}")

# Also try yfinance Search if available
try:
    print("\n--- Trying yf.Search for 'Tata Motors' ---")
    s_tata = yf.Search("Tata Motors", max_results=5)
    for q in s_tata.quotes:
        print(f"   Search Quote: symbol={q.get('symbol')}, shortname={q.get('shortname')}, exchange={q.get('exchange')}")
        ticker_results.append(f"Search 'Tata Motors': symbol={q.get('symbol')}, name={q.get('shortname')}, exchange={q.get('exchange')}")
except Exception as e:
    print(f"Search Tata Motors failed: {e}")

try:
    print("\n--- Trying yf.Search for 'Zomato' / 'Eternal' ---")
    s_zomato = yf.Search("Zomato", max_results=5)
    for q in s_zomato.quotes:
        print(f"   Search Quote (Zomato): symbol={q.get('symbol')}, shortname={q.get('shortname')}, exchange={q.get('exchange')}")
        ticker_results.append(f"Search 'Zomato': symbol={q.get('symbol')}, name={q.get('shortname')}, exchange={q.get('exchange')}")
    s_eternal = yf.Search("Eternal", max_results=5)
    for q in s_eternal.quotes:
        print(f"   Search Quote (Eternal): symbol={q.get('symbol')}, shortname={q.get('shortname')}, exchange={q.get('exchange')}")
        ticker_results.append(f"Search 'Eternal': symbol={q.get('symbol')}, name={q.get('shortname')}, exchange={q.get('exchange')}")
except Exception as e:
    print(f"Search Zomato/Eternal failed: {e}")

with open(f"{output_dir}/tatamotors_zomato_tickers.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(ticker_results))

print(f"\nSaved ticker tests to {output_dir}/tatamotors_zomato_tickers.txt")

