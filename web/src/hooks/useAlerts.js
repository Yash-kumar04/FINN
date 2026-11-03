import { useMemo } from 'react'

/**
 * Computes per-ticker alert flags purely from stored OHLCV data.
 * Returns a Map: symbol -> { priceChgPct, volRatio, priceAlert, volAlert }
 *
 * @param {object} pricesData - full prices.json object
 * @param {number} priceThr   - price move threshold in % (e.g. 3)
 * @param {number} volThr     - volume spike multiplier (e.g. 2.0)
 */
export function useAlerts(pricesData, priceThr, volThr) {
  return useMemo(() => {
    const map = new Map()
    if (!pricesData?.tickers) return map

    // prices.json has tickers as a dict keyed by "RELIANCE.NS" etc.
    for (const [symbol, t] of Object.entries(pricesData.tickers)) {
      const m = t.metrics || {}

      // Primary signal from precomputed metrics
      const priceChgPct = m.price_change_pct ?? null
      const volRatio    = m.volume_ratio    ?? null

      // Strip .NS suffix for matching with announcement ticker field
      const shortSym = symbol.replace(/\.NS$/, '')

      const entry = {
        priceChgPct,
        volRatio,
        priceAlert: priceChgPct != null && Math.abs(priceChgPct) >= priceThr,
        volAlert:   volRatio    != null && volRatio >= volThr,
        lastClose:  m.last_close,
        provisional: m.is_provisional || false,
        asOf: t.provenance?.as_of_date,
      }

      // Index by both "RELIANCE.NS" and "RELIANCE" for flexible lookup
      map.set(symbol, entry)
      map.set(shortSym, entry)
    }
    return map
  }, [pricesData, priceThr, volThr])
}
