import { useState, useMemo, useEffect } from 'react'
import {
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Flame,
  RotateCcw,
  Bell,
  Check,
} from 'lucide-react'
import clsx from 'clsx'
import { useSnapshot } from '../hooks/useSnapshot.js'
import { useAlerts } from '../hooks/useAlerts.js'
import {
  useAlertSettings,
  ALERT_CATEGORIES,
  DEFAULT_ALERT_SETTINGS,
  computeFiredAlerts,
} from '../hooks/useAlertSettings.js'
import { categoryMeta, timeAgo, fmtPct, fmtScore } from '../utils/format.js'
import EventCard from '../components/EventCard.jsx'
import AlertBanner from '../components/AlertBanner.jsx'

const WINDOWS = [
  { label: '24h', hours: 24 },
  { label: '3D',  hours: 72 },
  { label: '7D',  hours: 168 },
  { label: '30D', hours: 720 },
]

export default function BriefingTab({ onAlertsCountChange }) {
  const { data: ann, loading: annLoading, error: annError } = useSnapshot('announcements.json')
  const { data: prices } = useSnapshot('prices.json')
  const { data: resultsData } = useSnapshot('results.json')

  // Persisted alert settings in localStorage
  const {
    priceThr,
    volThr,
    categories: alertCategories,
    setPriceThr,
    setVolThr,
    toggleCategory,
    resetToDefaults,
  } = useAlertSettings()

  const [windowIdx, setWindowIdx] = useState(0)
  const [showSettings, setShowSettings] = useState(false)
  const [expandedRoutine, setExpandedRoutine] = useState(false)
  const [dismissedAlerts, setDismissedAlerts] = useState(() => new Set())

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
              status: res.status,
            },
          }
        }
        return ev
      })
  }, [ann, cutoff, resultsData])

  // Tier split — use primary_category field
  const tier1 = events.filter(e => categoryMeta(e.primary_category).tier === 1)
  const tier2 = events.filter(e => categoryMeta(e.primary_category).tier === 2)
  const tier3 = events.filter(e => categoryMeta(e.primary_category).tier === 3)

  // Recompute fired alerts purely client-side from snapshot data + settings
  const allFiredAlerts = useMemo(() => {
    return computeFiredAlerts(
      prices,
      ann,
      { priceThr, volThr, categories: alertCategories },
      anchorTime
    )
  }, [prices, ann, priceThr, volThr, alertCategories, anchorTime])

  // Inform parent / header about today's fired alerts count
  useEffect(() => {
    if (onAlertsCountChange) {
      onAlertsCountChange(allFiredAlerts.length)
    }
  }, [allFiredAlerts.length, onAlertsCountChange])

  // Filter out manually dismissed alert banners
  const visibleAlerts = useMemo(() => {
    return allFiredAlerts.filter(a => !dismissedAlerts.has(a.id))
  }, [allFiredAlerts, dismissedAlerts])

  const handleScrollToEvent = (eventId) => {
    const el = document.getElementById(eventId)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el.classList.add('ring-2', 'ring-accent', 'transition-all', 'duration-500')
      setTimeout(() => {
        el.classList.remove('ring-2', 'ring-accent')
      }, 2000)
    }
  }

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
      {/* Window picker + Alert settings toggle */}
      <div className="sticky top-0 z-30 bg-surface border-b border-border shadow-sm">
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
            onClick={() => setShowSettings(s => !s)}
            className={clsx(
              'ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors border',
              showSettings
                ? 'bg-accent/20 border-accent/40 text-accent'
                : 'bg-card border-border/80 text-muted hover:text-white'
            )}
          >
            <SlidersHorizontal size={12} />
            <span>Alerts</span>
            {allFiredAlerts.length > 0 && (
              <span className="w-4 h-4 rounded-full bg-accent text-[10px] text-white flex items-center justify-center font-bold ml-0.5">
                {allFiredAlerts.length}
              </span>
            )}
          </button>
        </div>

        {/* Expandable Alert Settings Panel (saved in localStorage) */}
        {showSettings && (
          <div className="px-4 py-3.5 flex flex-col gap-3.5 bg-card border-t border-border animate-in fade-in slide-in-from-top-1 duration-200">
            {/* Category Checkboxes */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-white uppercase tracking-wider">
                  Announcement Categories to Alert
                </span>
                <span className="text-[10px] text-muted font-mono">
                  {alertCategories.length} selected
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {ALERT_CATEGORIES.map(cat => {
                  const isChecked = alertCategories.includes(cat.id)
                  const meta = categoryMeta(cat.id)
                  return (
                    <label
                      key={cat.id}
                      className={clsx(
                        'flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs cursor-pointer select-none transition-all',
                        isChecked
                          ? 'bg-accent/10 border-accent/40 text-white'
                          : 'bg-surface/50 border-border/50 text-muted hover:text-white'
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleCategory(cat.id)}
                        className="rounded border-border text-accent focus:ring-0 w-3.5 h-3.5 accent-accent"
                      />
                      <span className={clsx('chip text-[9px] py-0 px-1.5', meta.chip)}>
                        {cat.label}
                      </span>
                    </label>
                  )
                })}
              </div>
            </div>

            {/* Price Move Slider */}
            <div className="pt-2 border-t border-border/60">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-white/90 font-medium">Price Move Threshold</span>
                <span className="font-mono text-xs text-accent font-semibold">≥ {priceThr}%</span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={1}
                  max={15}
                  step={0.5}
                  value={priceThr}
                  onChange={e => setPriceThr(e.target.value)}
                  className="flex-1 accent-accent"
                />
              </div>
            </div>

            {/* Volume Spike Slider */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-white/90 font-medium">Volume Spike Threshold</span>
                <span className="font-mono text-xs text-accent font-semibold">≥ {volThr.toFixed(1)}× prior 20d avg</span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={1.5}
                  max={8}
                  step={0.5}
                  value={volThr}
                  onChange={e => setVolThr(e.target.value)}
                  className="flex-1 accent-accent"
                />
              </div>
            </div>

            {/* Reset to Defaults button & Persistence Note */}
            <div className="flex items-center justify-between pt-2 border-t border-border/60 text-xs">
              <button
                onClick={resetToDefaults}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-surface border border-border text-muted hover:text-white transition-colors text-[11px]"
              >
                <RotateCcw size={11} />
                <span>Reset to defaults</span>
              </button>
              <span className="text-[10px] text-muted font-mono flex items-center gap-1">
                <Check size={11} className="text-positive" />
                <span>Saved in localStorage</span>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Fired Alert Banners Stack */}
      {visibleAlerts.length > 0 && (
        <div className="px-3 pt-3 flex flex-col gap-2">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-semibold text-white flex items-center gap-1.5">
              <Bell size={13} className="text-accent" />
              <span>Today's Fired Alerts</span>
              <span className="chip chip-other text-[10px] font-mono py-0">{visibleAlerts.length}</span>
            </span>
            {dismissedAlerts.size > 0 && (
              <button
                onClick={() => setDismissedAlerts(new Set())}
                className="text-[10px] text-muted hover:text-accent font-mono transition-colors"
              >
                Restore {dismissedAlerts.size} dismissed
              </button>
            )}
          </div>
          <div className="flex flex-col gap-2">
            {visibleAlerts.map(alert => (
              <AlertBanner
                key={alert.id}
                alert={alert}
                onDismiss={id => setDismissedAlerts(s => new Set(s).add(id))}
                onScrollToEvent={handleScrollToEvent}
              />
            ))}
          </div>
        </div>
      )}

      {/* Tier 1 Events */}
      {tier1.length > 0 && (
        <section className="px-3 pt-4">
          <SectionHeader label="Important" count={tier1.length} />
          <div className="flex flex-col gap-3 mt-2">
            {tier1
              .sort((a, b) => (b.importance_score ?? 0) - (a.importance_score ?? 0))
              .map(ev => (
                <EventCard
                  key={ev.event_id}
                  event={ev}
                  alertData={alerts.get(ev.ticker)}
                  anchorTime={anchorTime}
                />
              ))}
          </div>
        </section>
      )}

      {/* Tier 2 Events */}
      {tier2.length > 0 && (
        <section className="px-3 pt-4">
          <SectionHeader label="Updates" count={tier2.length} />
          <div className="flex flex-col gap-2 mt-2">
            {tier2
              .sort((a, b) => (b.importance_score ?? 0) - (a.importance_score ?? 0))
              .map(ev => (
                <EventCard
                  key={ev.event_id}
                  event={ev}
                  alertData={alerts.get(ev.ticker)}
                  anchorTime={anchorTime}
                  compact
                />
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
                  <EventCard
                    key={ev.event_id}
                    event={ev}
                    alertData={alerts.get(ev.ticker)}
                    anchorTime={anchorTime}
                    compact
                    minimal
                  />
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
      <span className="font-semibold text-xs tracking-wider uppercase text-white/70">{label}</span>
      <span className="chip chip-other text-[10px] font-mono py-0">{count}</span>
    </div>
  )
}
