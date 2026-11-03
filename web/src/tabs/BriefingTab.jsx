import { useState, useMemo } from 'react'
import { SlidersHorizontal, ChevronDown, ChevronUp, AlertTriangle, TrendingDown, TrendingUp, Flame } from 'lucide-react'
import clsx from 'clsx'
import { useSnapshot } from '../hooks/useSnapshot.js'
import { useAlerts } from '../hooks/useAlerts.js'
import { categoryMeta, timeAgo, fmtPct, fmtScore } from '../utils/format.js'
import EventCard from '../components/EventCard.jsx'
import AlertBanner from '../components/AlertBanner.jsx'

const WINDOWS = [
  { label: '24h', hours: 24 },
  { label: '3D',  hours: 72 },
  { label: '7D',  hours: 168 },
  { label: '30D', hours: 720 },
]

export default function BriefingTab() {
  const { data: ann, loading: annLoading, error: annError } = useSnapshot('announcements.json')
  const { data: prices } = useSnapshot('prices.json')
  const { data: resultsData } = useSnapshot('results.json')

  const [windowIdx, setWindowIdx]   = useState(0)
  const [priceThr, setPriceThr]     = useState(3)
  const [volThr, setVolThr]         = useState(2.0)
  const [showSliders, setShowSliders] = useState(false)
  const [expandedRoutine, setExpandedRoutine] = useState(false)

  const alerts = useAlerts(prices, priceThr, volThr)

  // Anchor window picker to snapshot's latest filing timestamp
  const anchorTime = useMemo(() => {
    if (!ann?.events?.length) return new Date()
    let maxMs = 0
    for (const ev of ann.events) {
      if (ev.timestamp) {
        const ms = new Date(ev.timestamp.replace(/-/g, ' ')).getTime()
        if (!isNaN(ms) && ms > maxMs) maxMs = ms
      }
    }
    return maxMs > 0 ? new Date(maxMs) : new Date()
  }, [ann])

  // Filter events by time window anchored to snapshot
  const windowHours = WINDOWS[windowIdx].hours
  const cutoff = useMemo(() => new Date(anchorTime.getTime() - windowHours * 3600 * 1000), [anchorTime, windowHours])

  const events = useMemo(() => {
    if (!ann?.events) return []
    return ann.events
      .filter(ev => {
        // timestamp is like "30-Oct-2026 19:40:11" — parse it
        const ts = ev.timestamp
        if (!ts) return true
        const parsed = new Date(ts.replace(/-/g, ' '))
        if (isNaN(parsed)) return true
        return parsed >= cutoff
      })
      .map(ev => {
        const res = resultsData?.[ev.ticker]
        if (res && ev.primary_category === 'results' && !ev.results && res.status === 'verified') {
          return {
            ...ev,
            results: {
              period: res.period,
              type: res.scope,
              revenue: `₹${res.metrics.revenue.current_quarter.toLocaleString()} Cr`,
              ebitda: `₹${res.metrics.ebitda.current_quarter.toLocaleString()} Cr`,
              pbt: `₹${res.metrics.pbt.current_quarter.toFixed(2)} Cr`,
              pat: `₹${res.metrics.pat.current_quarter.toFixed(2)} Cr`,
              revenue_qoq_pct: res.metrics.revenue.qoq_pct,
              revenue_yoy_pct: res.metrics.revenue.yoy_pct,
              ebitda_qoq_pct: res.metrics.ebitda.qoq_pct,
              ebitda_yoy_pct: res.metrics.ebitda.yoy_pct,
              pbt_qoq_pct: res.metrics.pbt.qoq_pct,
              pbt_yoy_pct: res.metrics.pbt.yoy_pct,
              pat_qoq_pct: res.metrics.pat.qoq_pct,
              pat_yoy_pct: res.metrics.pat.yoy_pct,
              source_url: res.provenance?.source_url,
              filing_page: res.provenance?.filing_pages?.[2] || 11,
              status: res.status
            }
          }
        }
        return ev
      })
  }, [ann, cutoff, resultsData])

  // Tier split — use primary_category field
  const tier1 = events.filter(e => categoryMeta(e.primary_category).tier === 1)
  const tier2 = events.filter(e => categoryMeta(e.primary_category).tier === 2)
  const tier3 = events.filter(e => categoryMeta(e.primary_category).tier === 3)

  // Alerts that fired — events use `ticker` field like "RELIANCE.NS"
  const firedPriceAlerts = [...alerts.entries()]
    .filter(([k, v]) => v.priceAlert && k.includes('.NS'))
  const firedVolAlerts = [...alerts.entries()]
    .filter(([k, v]) => v.volAlert && k.includes('.NS'))

  if (annLoading) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Loading snapshot…
      </div>
    )
  }

  if (annError) {
    return (
      <div className="p-4 text-negative text-sm">
        Failed to load snapshot: {annError}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-0">
      {/* Window picker + sliders toggle */}
      <div className="sticky top-0 z-30 bg-surface border-b border-border">
        <div className="flex items-center gap-2 px-4 py-2">
          {WINDOWS.map((w, i) => (
            <button
              key={w.label}
              onClick={() => setWindowIdx(i)}
              className={clsx(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                i === windowIdx
                  ? 'bg-accent text-white'
                  : 'bg-card text-muted hover:text-white'
              )}
            >
              {w.label}
            </button>
          ))}
          <button
            onClick={() => setShowSliders(s => !s)}
            className={clsx(
              'ml-auto flex items-center gap-1 px-2 py-1 rounded-full text-xs transition-colors',
              showSliders ? 'bg-accent/20 text-accent' : 'bg-card text-muted hover:text-white'
            )}
          >
            <SlidersHorizontal size={12} />
            Alerts
          </button>
        </div>

        {/* Sliders */}
        {showSliders && (
          <div className="px-4 pb-3 flex flex-col gap-3 bg-card border-t border-border">
            <div className="flex items-center gap-3 pt-3">
              <span className="text-xs text-muted w-28 shrink-0">Price ≥ {priceThr}%</span>
              <input
                type="range" min={1} max={10} step={0.5} value={priceThr}
                onChange={e => setPriceThr(+e.target.value)}
                className="flex-1 accent-accent"
              />
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted w-28 shrink-0">Vol spike ≥ {volThr.toFixed(1)}×</span>
              <input
                type="range" min={1.5} max={5} step={0.5} value={volThr}
                onChange={e => setVolThr(+e.target.value)}
                className="flex-1 accent-accent"
              />
            </div>
          </div>
        )}
      </div>

      {/* Alert banners */}
      {(firedPriceAlerts.length > 0 || firedVolAlerts.length > 0) && (
        <div className="px-3 pt-3 flex flex-col gap-2">
          {firedPriceAlerts.map(([sym, v]) => (
            <AlertBanner key={sym + '-price'} symbol={sym} alertData={v} type="price" threshold={priceThr} />
          ))}
          {firedVolAlerts.map(([sym, v]) => (
            <AlertBanner key={sym + '-vol'} symbol={sym} alertData={v} type="vol" threshold={volThr} />
          ))}
        </div>
      )}

      {/* Tier 1 */}
      {tier1.length > 0 && (
        <section className="px-3 pt-4">
          <SectionHeader label="Important" count={tier1.length} />
          <div className="flex flex-col gap-3 mt-2">
            {tier1
              .sort((a, b) => (b.importance_score ?? 0) - (a.importance_score ?? 0))
              .map(ev => (
                <EventCard key={ev.event_id} event={ev} alertData={alerts.get(ev.ticker)} anchorTime={anchorTime} />
              ))}
          </div>
        </section>
      )}

      {/* Tier 2 */}
      {tier2.length > 0 && (
        <section className="px-3 pt-4">
          <SectionHeader label="Updates" count={tier2.length} />
          <div className="flex flex-col gap-2 mt-2">
            {tier2
              .sort((a, b) => (b.importance_score ?? 0) - (a.importance_score ?? 0))
              .map(ev => (
                <EventCard key={ev.event_id} event={ev} alertData={alerts.get(ev.ticker)} anchorTime={anchorTime} compact />
              ))}
          </div>
        </section>
      )}

      {/* Tier 3 — collapsed by default */}
      {tier3.length > 0 && (
        <section className="px-3 pt-4 pb-4">
          <button
            onClick={() => setExpandedRoutine(r => !r)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-card border border-border text-muted text-sm hover:text-white transition-colors"
          >
            <span>{tier3.length} routine filings — tap to {expandedRoutine ? 'collapse' : 'expand'}</span>
            {expandedRoutine ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {expandedRoutine && (
            <div className="flex flex-col gap-1 mt-2">
              {tier3
                .sort((a, b) => (b.importance_score ?? 0) - (a.importance_score ?? 0))
                .map(ev => (
                  <EventCard key={ev.event_id} event={ev} alertData={alerts.get(ev.ticker)} anchorTime={anchorTime} compact minimal />
                ))}
            </div>
          )}
        </section>
      )}

      {events.length === 0 && (
        <div className="px-4 py-12 text-center text-muted text-sm">
          No announcements in the last {WINDOWS[windowIdx].label} window.
        </div>
      )}

      {/* Snapshot provenance footer */}
      {ann?.provenance && (
        <div className="px-4 py-3 border-t border-border text-[10px] text-muted font-mono">
          Snapshot: {ann.provenance.fetched_at_ist} ·{' '}
          {ann.events?.length} events ·{' '}
          {ann.stats?.total_filings ?? ann.total_announcements ?? '—'} filings
        </div>
      )}
    </div>
  )
}

function SectionHeader({ label, count }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs font-semibold uppercase tracking-widest text-muted">{label}</span>
      <span className="chip chip-other">{count}</span>
      <div className="flex-1 h-px bg-border" />
    </div>
  )
}
