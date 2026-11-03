import yfinance as yf
for sym in ['RELIANCE.NS', 'DIXON.NS', 'TRENT.NS']:
    t = yf.Ticker(sym)
    print(f"=== {sym} ===")
    h1 = t.history(period="1mo")
    print("history(1mo) tail(3):")
    print(h1.tail(3)[['Open', 'High', 'Low', 'Close', 'Volume']])
    h2 = t.history(period="3mo")
    print("history(3mo) tail(3):")
    print(h2.tail(3)[['Open', 'High', 'Low', 'Close', 'Volume']])

