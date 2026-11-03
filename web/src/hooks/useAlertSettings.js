import { useState, useEffect, useMemo, useCallback } from 'react'

export const ALERT_CATEGORIES = [
  { id: 'results', label: 'Results', desc: 'Earnings & financial statements' },
  { id: 'management_change', label: 'Management', desc: 'Director/KMP appointments & exits' },
  { id: 'M&A', label: 'M&A', desc: 'Acquisitions, amalgamations, restructuring' },
  { id: 'fund_raise', label: 'Fund Raise', desc: 'QIP, rights, warrants, debt issues' },
  { id: 'litigation', label: 'Litigation', desc: 'Regulatory, CIRP, court orders' },
  { id: 'credit_rating', label: 'Credit Rating', desc: 'Upgrades, downgrades, outlook' },
  { id: 'dividend', label: 'Dividend', desc: 'Interim/final dividend announcements' },
]

export const DEFAULT_ALERT_SETTINGS = {
  priceThr: 3.0,
  volThr: 2.0,
  categories: ['results', 'management_change', 'M&A', 'litigation'],
}

const STORAGE_KEY = 'finn_alert_settings'

export function useAlertSettings() {
  const [settings, setSettings] = useState(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const saved = window.localStorage.getItem(STORAGE_KEY)
        if (saved) {
          const parsed = JSON.parse(saved)
          return {
            priceThr: typeof parsed.priceThr === 'number' ? parsed.priceThr : DEFAULT_ALERT_SETTINGS.priceThr,
            volThr: typeof parsed.volThr === 'number' ? parsed.volThr : DEFAULT_ALERT_SETTINGS.volThr,
            categories: Array.isArray(parsed.categories) ? parsed.categories : DEFAULT_ALERT_SETTINGS.categories,
          }
        }
      }
    } catch (e) {
      console.warn('Failed to read localStorage alert settings:', e)
    }
    return DEFAULT_ALERT_SETTINGS
  })

  // Sync to localStorage
  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
      }
    } catch (e) {
      console.warn('Failed to save localStorage alert settings:', e)
    }
  }, [settings])

  const setPriceThr = useCallback((val) => {
    setSettings(s => ({ ...s, priceThr: Number(val) }))
  }, [])

  const setVolThr = useCallback((val) => {
    setSettings(s => ({ ...s, volThr: Number(val) }))
  }, [])

  const toggleCategory = useCallback((catId) => {
    setSettings(s => {
      const exists = s.categories.includes(catId)
      const next = exists ? s.categories.filter(c => c !== catId) : [...s.categories, catId]
      return { ...s, categories: next }
    })
  }, [])

  const resetToDefaults = useCallback(() => {
    setSettings(DEFAULT_ALERT_SETTINGS)
  }, [])

  return {
    priceThr: settings.priceThr,
    volThr: settings.volThr,
    categories: settings.categories,
    setPriceThr,
    setVolThr,
    toggleCategory,
    resetToDefaults,
  }
}

/**
 * Pure client-side alert computation from snapshots
 * Combines market moves (prices.json) and category announcements (announcements.json)
 */
export function computeFiredAlerts(pricesData, annData, settings, anchorTime = null) {
  if (!pricesData?.tickers) return []

  const alerts = []
  const events = annData?.events || []
  const { priceThr, volThr, categories } = settings

  // 1. Map events by ticker for linking
  const tickerEvents = new Map()
  for (const ev of events) {
    if (!tickerEvents.has(ev.ticker)) {
      tickerEvents.set(ev.ticker, [])
    }
    tickerEvents.get(ev.ticker).push(ev)
  }

  // 2. Evaluate market move alerts from prices.json
  for (const [sym, td] of Object.entries(pricesData.tickers)) {
    const m = td.metrics || {}
    const priceChg = m.price_change_pct ?? 0
    const volRatio = m.volume_ratio ?? 1.0
    const shortSym = sym.replace(/\.NS$/, '')

    const priceFired = Math.abs(priceChg) >= priceThr
    const volFired = volRatio >= volThr

    if (priceFired || volFired) {
      // Find latest relevant event for this ticker
      const matchingEvents = tickerEvents.get(sym) || []
      const primaryEvent = matchingEvents[0] || null

      alerts.push({
        id: `mkt-${sym}`,
        ticker: sym,
        symbol: shortSym,
        kind: priceFired && volFired ? 'combined' : (priceFired ? 'price' : 'volume'),
        priceChgPct: priceChg,
        volRatio: volRatio,
        priceFired,
        volFired,
        title: primaryEvent ? primaryEvent.title : `${shortSym} Significant Market Movement`,
        eventId: primaryEvent ? primaryEvent.event_id : null,
        filingUrl: primaryEvent?.primary_filing?.attachment_url || null,
        timestamp: primaryEvent?.timestamp || td.provenance?.as_of_date || '2026-11-02',
        companyName: td.name || shortSym,
      })
    }
  }

  // 3. Evaluate category announcement alerts in the latest session / 24h
  // Anchor cutoff: 24h before anchorTime (or latest filing timestamp)
  const anchorMs = anchorTime ? anchorTime.getTime() : Date.now()
  const cutoff24h = anchorMs - 24 * 3600 * 1000

  for (const ev of events) {
    if (!categories.includes(ev.primary_category)) continue

    // Parse event timestamp
    let isRecent = false
    if (ev.timestamp) {
      const ms = new Date(ev.timestamp.replace(/-/g, ' ')).getTime()
      if (!isNaN(ms) && ms >= cutoff24h) {
        isRecent = true
      }
    }

    if (isRecent) {
      // Check if already covered by market alert for same event
      const alreadyCovered = alerts.some(a => a.eventId === ev.event_id)
      if (!alreadyCovered) {
        const shortSym = ev.ticker.replace(/\.NS$/, '')
        const m = pricesData.tickers[ev.ticker]?.metrics || {}
        alerts.push({
          id: `ann-${ev.event_id}`,
          ticker: ev.ticker,
          symbol: shortSym,
          kind: 'category',
          category: ev.primary_category,
          priceChgPct: m.price_change_pct ?? null,
          volRatio: m.volume_ratio ?? null,
          title: ev.title,
          eventId: ev.event_id,
          filingUrl: ev.primary_filing?.attachment_url || null,
          timestamp: ev.timestamp,
          companyName: ev.company_name || shortSym,
        })
      }
    }
  }

  // Sort alerts: combined first, then high vol/price moves, then category alerts
  alerts.sort((a, b) => {
    const scoreA = (a.kind === 'combined' ? 100 : 0) + (a.volRatio || 0) * 10 + Math.abs(a.priceChgPct || 0)
    const scoreB = (b.kind === 'combined' ? 100 : 0) + (b.volRatio || 0) * 10 + Math.abs(b.priceChgPct || 0)
    return scoreB - scoreA
  })

  return alerts
}

