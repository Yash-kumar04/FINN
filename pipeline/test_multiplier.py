import json
from datetime import datetime, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")
def parse_ts(ts_str):
    try:
        return datetime.strptime(ts_str, "%d-%b-%Y %H:%M:%S").replace(tzinfo=IST)
    except:
        return None

# Load prices trimmed to 2026-11-02
prices_raw = json.load(open('web/public/data/prices.json', encoding='utf-8'))
trimmed_prices = {}
for sym, td in prices_raw['tickers'].items():
    bars = [b for b in td['bars'] if b['date'] <= '2026-11-02']
    last_bar = bars[-1]
    prev_bar = bars[-2]
    prior20 = [b['volume'] for b in bars[-21:-1]]
    avg20 = sum(prior20) / len(prior20)
    vol_ratio = last_bar['volume'] / avg20 if avg20 > 0 else 1.0
    price_chg = ((last_bar['close'] - prev_bar['close']) / prev_bar['close']) * 100.0
    trimmed_prices[sym] = {
        'last_close': last_bar['close'],
        'last_volume': last_bar['volume'],
        'price_change_pct': price_chg,
        'volume_20d_avg': avg20,
        'volume_ratio': vol_ratio,
        'as_of_date': last_bar['date'],
        'weight': td.get('portfolio_weight', 0.05)
    }

# Let's test a clean, unconstrained or higher-ceiling multiplier
# If we test:
# multiplier = 1.0 + vol_boost * 0.25 + abs(price_chg) * 0.10
# For RELIANCE: vol_boost = 4.83 -> 4.83 * 0.25 = 1.208; price = 11.60 -> 11.60 * 0.10 = 1.160 -> mult = 3.368
# RELIANCE score: 1.0 * 0.12 * 3.368 * 100 = 40.42
# For DIXON: vol_boost = 4.95 -> 4.95 * 0.25 = 1.238; price = 11.99 -> 11.99 * 0.10 = 1.199 -> mult = 3.437
# DIXON score: 1.0 * 0.04 * 3.437 * 100 = 13.75
# For HDFCBANK: vol_boost = 0; price = 1.04 -> mult = 1.104
# HDFC mgmt score: 0.9 * 0.10 * 1.104 * 100 = 9.94
# For LT: vol_boost = 0; price = 1.76 -> mult = 1.176
# LT M&A score: 0.9 * 0.08 * 1.176 * 100 = 8.47

print("Formula: multiplier = 1.0 + min(max(vol_ratio - 1.0, 0), 5.0) * 0.25 + min(abs(price_chg), 15.0) * 0.10")
for sym in ['RELIANCE.NS', 'DIXON.NS', 'HDFCBANK.NS', 'LT.NS', 'CDSL.NS']:
    m = trimmed_prices[sym]
    vr = m['volume_ratio']
    pc = m['price_change_pct']
    pw = m['weight']
    vol_comp = min(max(vr - 1.0, 0.0), 5.0) * 0.25
    price_comp = min(abs(pc), 15.0) * 0.10
    mult = 1.0 + vol_comp + price_comp
    score_res = 1.0 * pw * mult * 100
    print(f"  {sym:<15} mult={mult:.3f}  score(results)={score_res:.2f}")
