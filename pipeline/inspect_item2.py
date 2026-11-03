import json

prices = json.load(open('web/public/data/prices.json', encoding='utf-8'))
for sym in ['RELIANCE.NS', 'DIXON.NS', 'CDSL.NS', 'SUNPHARMA.NS']:
    td = prices['tickers'][sym]
    # find bars <= 2026-11-02
    bars = [b for b in td['bars'] if b['date'] <= '2026-11-02']
    bar_nov2 = bars[-1]
    baseline_20 = bars[-21:-1]
    num = bar_nov2['volume']
    base_dates = [b['date'] for b in baseline_20]
    denom = sum(b['volume'] for b in baseline_20) / len(baseline_20)
    ratio = num / denom
    prev_bar = bars[-2]
    price_chg = ((bar_nov2['close'] - prev_bar['close']) / prev_bar['close']) * 100
    print(f'{sym}:')
    print(f'  numerator (vol on {bar_nov2["date"]}): {num:,}')
    print(f'  20 baseline dates: {base_dates}')
    print(f'  denominator (mean 20d): {denom:,.2f}')
    print(f'  volume_ratio: {ratio:.4f}')
    print(f'  price_change_pct: {price_chg:.2f}%')
    print(f'  Fires at 3% / 2x defaults? price_chg >= 3%: {abs(price_chg) >= 3.0}, vol >= 2x: {ratio >= 2.0}')
    print()

