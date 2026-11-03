import json

prices = json.load(open('web/public/data/prices.json', encoding='utf-8'))
tickers = ['RELIANCE.NS', 'DIXON.NS', 'CDSL.NS', 'SUNPHARMA.NS']

print("=" * 80)
print("ITEM 2: VOLUME RATIO (20 SESSIONS STRICTLY BEFORE 2026-11-02)")
print("=" * 80)

for sym in tickers:
    td = prices['tickers'][sym]
    bars = td['bars']
    assert bars[-1]['date'] == '2026-11-02', f"Expected last bar 2026-11-02, got {bars[-1]['date']}"
    
    last_bar = bars[-1]
    prev_bar = bars[-2]
    numerator = last_bar['volume']
    
    baseline_bars = bars[-21:-1]
    assert len(baseline_bars) == 20, f"Expected 20 baseline bars, got {len(baseline_bars)}"
    baseline_dates = [b['date'] for b in baseline_bars]
    baseline_volumes = [b['volume'] for b in baseline_bars]
    mean_baseline = sum(baseline_volumes) / 20.0
    
    calc_ratio = numerator / mean_baseline
    stored_ratio = td['metrics']['volume_ratio']
    stored_avg = td['metrics']['volume_20d_avg']
    
    price_change_pct = ((last_bar['close'] - prev_bar['close']) / prev_bar['close']) * 100.0
    
    price_alert = abs(price_change_pct) >= 3.0
    vol_alert = calc_ratio >= 2.0
    
    print(f"Ticker: {sym}")
    print(f"  Numerator (volume on {last_bar['date']}): {numerator:,}")
    print(f"  20 Baseline Dates ({len(baseline_dates)} sessions strictly before 2026-11-02):")
    print(f"    {baseline_dates}")
    print(f"  Mean Baseline Volume (20d): {mean_baseline:,.2f}  [stored: {stored_avg:,.2f}]")
    print(f"  Volume Ratio: {calc_ratio:.4f}  [stored: {stored_ratio:.4f}]")
    print(f"  1-Day Price Change: {price_change_pct:+.2f}% (Close {prev_bar['close']} -> {last_bar['close']})")
    print(f"  Alert Status at defaults (Price +/-3%, Vol >= 2.0x):")
    print(f"    Price Alert Fired: {price_alert} (|{price_change_pct:.2f}%| >= 3.0%)")
    print(f"    Volume Alert Fired: {vol_alert} ({calc_ratio:.2f}x >= 2.0x)")
    print(f"    Both Fired: {price_alert and vol_alert}")
    print()

