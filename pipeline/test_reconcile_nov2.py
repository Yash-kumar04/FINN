import yfinance as yf
import pandas as pd

for sym in ['RELIANCE.NS', 'DIXON.NS', 'TRENT.NS']:
    t = yf.Ticker(sym)
    fi = t.fast_info
    print(f"\n=== {sym} FAST INFO ===")
    print(f"open: {fi.open}, day_high: {fi.day_high}, day_low: {fi.day_low}, last_price: {fi.last_price}, last_volume: {fi.last_volume}")
    
    # Check hourly bars
    h_1h = t.history(period="3d", interval="1h")
    # Filter for 2026-11-02
    h_nov2 = h_1h[h_1h.index.strftime('%Y-%m-%d') == '2026-11-02']
    if not h_nov2.empty:
        open_val = float(h_nov2['Open'].iloc[0])
        high_val = float(h_nov2['High'].max())
        low_val = float(h_nov2['Low'].min())
        close_val = float(h_nov2['Close'].iloc[-1])
        vol_val = int(h_nov2['Volume'].sum())
        print(f"Hourly aggregated Nov 2: Open={open_val}, High={high_val}, Low={low_val}, Close={close_val}, Vol={vol_val}")
