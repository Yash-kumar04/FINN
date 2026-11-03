import yfinance as yf
t = yf.Ticker("RELIANCE.NS")
print("fast_info:", dict(t.fast_info) if hasattr(t, "fast_info") else "no fast_info")
h_1d = t.history(period="5d", interval="1d")
print("history 5d 1d interval:\n", h_1d)
h_1h = t.history(period="5d", interval="1h")
print("history 5d 1h interval tail(5):\n", h_1h.tail(5) if not h_1h.empty else "empty 1h")

