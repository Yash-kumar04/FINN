import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, Paperclip } from 'lucide-react'
import clsx from 'clsx'
import { categoryMeta, timeAgo, fmtPct, fmtScore, deltaClass } from '../utils/format.js'

export default function EventCard({ event, alertData, compact = false, minimal = false, anchorTime = null }) {
  const [expanded, setExpanded] = useState(false)

  // Field mapping: snapshot uses primary_category + ticker + title
  const category = event.primary_category || event.category || 'unclassified'
  const symbol   = (event.ticker || event.symbol || '').replace(/\.NS$/, '')
  const title    = event.title || event.primary_filing?.desc || event.desc || '—'
  const meta     = categoryMeta(category)
  const secondaryTags = (event.secondary_tags || []).filter(t => t !== category)

  // All filings = primary + supporting
  const allFilings = [
    ...(event.primary_filing ? [event.primary_filing] : []),
    ...(event.supporting_filings || []),
    ...(event.filings || []),
  ]

  const priceChgPct = alertData?.priceChgPct
  const volRatio    = alertData?.volRatio

  // Parse timestamp "30-Oct-2026 19:40:11"
  const tsDisplay = event.timestamp
    ? timeAgo(new Date(event.timestamp.replace(/-/g, ' ')), anchorTime)
    : ''

  if (minimal) {
    return (
      <div id={event.event_id} className="flex items-center gap-2 px-3 py-2 rounded bg-card/50 text-xs text-muted scroll-mt-20">
        <span className={clsx('chip text-[9px]', meta.chip)}>{meta.label}</span>
        <span className="font-medium text-white/70">{symbol}</span>
        <span className="flex-1 truncate">{title}</span>
        <span className="shrink-0 font-mono text-[10px]">{tsDisplay}</span>
      </div>
    )
  }

  if (compact) {
    return (
      <div id={event.event_id} className="flex items-start gap-3 px-3 py-2.5 rounded-lg bg-card border border-border scroll-mt-20">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={clsx('chip text-[10px]', meta.chip)}>{meta.label}</span>
            {secondaryTags.slice(0, 2).map(t => (
              <span key={t} className="chip chip-other text-[9px]">{t.replace('_', ' ')}</span>
            ))}
            <span className="font-semibold text-sm text-white">{symbol}</span>
            <span className="text-muted text-xs ml-auto shrink-0">{tsDisplay}</span>
          </div>
          <p className="text-xs text-muted mt-1 line-clamp-2">{title}</p>
        </div>
        {priceChgPct != null && (
          <span className={clsx('font-mono text-xs shrink-0', deltaClass(priceChgPct))}>
            {fmtPct(priceChgPct)}
          </span>
        )}
      </div>
    )
  }

  // Rich card for Tier 1
  return (
    <div id={event.event_id} className="rounded-xl bg-card border border-border overflow-hidden scroll-mt-20">
      <div className="px-4 pt-4 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className={clsx('chip', meta.chip)}>{meta.label}</span>
              {secondaryTags.slice(0, 3).map(t => (
                <span key={t} className="chip chip-other text-[9px]">{t.replace(/_/g, ' ')}</span>
              ))}
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-bold text-base text-white">{symbol}</span>
              {event.company_name && (
                <span className="text-muted text-xs truncate max-w-[120px]">{event.company_name}</span>
              )}
              <span className="text-muted text-xs ml-auto shrink-0">{tsDisplay}</span>
            </div>
            <p className="text-sm font-medium text-white/95 mt-1 leading-snug">{title}</p>
          </div>
          {/* Score */}
          <div className="text-right shrink-0 ml-2">
            <div className="text-[10px] text-muted uppercase tracking-wide">Score</div>
            <div className="font-mono font-semibold text-accent text-sm">{fmtScore(event.importance_score)}</div>
          </div>
        </div>

        {/* Score breakdown tooltip-style */}
        {event.score_breakdown && (
          <div className="flex items-center gap-3 mt-2 text-[10px] text-muted font-mono">
            <span>cat×{event.score_breakdown.category_weight}</span>
            <span>wt×{event.score_breakdown.portfolio_weight}</span>
            <span>mkt×{event.score_breakdown.market_reaction_multiplier?.toFixed(2)}</span>
          </div>
        )}

        {/* Market reaction row */}
        {(priceChgPct != null || volRatio != null) && (
          <div className="flex items-center gap-3 mt-3 pt-3 border-t border-border/50">
            <span className="text-[10px] text-muted uppercase tracking-wide">Market</span>
            {priceChgPct != null && (
              <span className={clsx('font-mono text-sm font-medium', deltaClass(priceChgPct))}>
                {fmtPct(priceChgPct)} price
              </span>
            )}
            {volRatio != null && (
              <span className={clsx(
                'font-mono text-sm font-medium',
                volRatio >= 2 ? 'text-warning' : 'text-muted'
              )}>
                {volRatio.toFixed(1)}× vol
              </span>
            )}
            {alertData?.provisional && (
              <span className="chip chip-other text-[9px] ml-auto">provisional</span>
            )}
          </div>
        )}

        {/* Results financials (filled in Step 5) */}
        {category === 'results' && (
          <ResultsStub results={event.results} />
        )}

        {/* Management change */}
        {(category === 'management_change' || secondaryTags.includes('management_change')) && (
          <MgmtStub mgmt={event.management_changes} />
        )}
      </div>

      {/* Expand toggle for filings */}
      {allFilings.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(e => !e)}
            className="w-full flex items-center justify-between px-4 py-2 border-t border-border text-xs text-muted hover:bg-white/5 transition-colors"
          >
            <span>{allFilings.length} filing{allFilings.length > 1 ? 's' : ''}</span>
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {expanded && (
            <div className="flex flex-col divide-y divide-border border-t border-border">
              {allFilings.map((f, i) => (
                <FilingRow key={f.seq_id || i} filing={f} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function ResultsStub({ results }) {
  if (!results || results.status === 'unverified') {
    return (
      <div className="mt-3 pt-3 border-t border-border/50">
        <div className="flex items-center justify-between text-xs text-muted bg-surface/40 px-3 py-2 rounded border border-border/40">
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0 inline-block" />
            <span className="line-clamp-1">Results: {results?.unverified_reason || 'Unverified'}</span>
          </span>
          {results?.source_url && (
            <a
              href={results.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-accent hover:underline font-mono text-[11px] shrink-0 ml-2"
            >
              <span>Filing PDF</span>
              <ExternalLink size={10} />
            </a>
          )}
        </div>
      </div>
    )
  }

  const fields = [
    { key: 'revenue', label: 'Revenue' },
    { key: 'ebitda',  label: 'EBITDA' },
    { key: 'pbt',     label: 'PBT' },
    { key: 'pat',     label: 'PAT' },
  ]

  return (
    <div className="mt-3 pt-3 border-t border-border/50">
      <div className="grid grid-cols-4 gap-1 text-center">
        {fields.map(({ key, label }) => {
          const v = results[key]
          const qoq = results[`${key}_qoq_pct`]
          const yoy = results[`${key}_yoy_pct`]
          return (
            <div key={key} className="flex flex-col gap-0.5 p-1 rounded bg-black/20">
              <span className="text-[9px] text-muted uppercase tracking-wide">{label}</span>
              <span className="font-mono text-xs font-semibold text-white">{v ?? '—'}</span>
              {qoq != null && (
                <span className={clsx('font-mono text-[9px] font-medium', qoq >= 0 ? 'text-positive' : 'text-negative')}>
                  QoQ {qoq >= 0 ? '+' : ''}{qoq.toFixed(1)}%
                </span>
              )}
              {yoy != null && (
                <span className={clsx('font-mono text-[9px] font-medium', yoy >= 0 ? 'text-positive' : 'text-negative')}>
                  YoY {yoy >= 0 ? '+' : ''}{yoy.toFixed(1)}%
                </span>
              )}
            </div>
          )
        })}
      </div>
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/30 text-[10px] text-muted">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-positive inline-block" />
          <span>{results.period || 'Q2 FY27'} · {results.type || 'Consolidated'}</span>
        </span>
        {results.source_url && (
          <a
            href={results.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-accent hover:underline font-mono"
          >
            <span>Filing PDF (p.{results.filing_page || 11})</span>
            <ExternalLink size={10} />
          </a>
        )}
      </div>
    </div>
  )
}

function MgmtStub({ mgmt }) {
  if (!mgmt) {
    return null
  }

  const items = Array.isArray(mgmt) ? mgmt : [mgmt]

  return (
    <div className="mt-3 pt-3 border-t border-border/50 flex flex-col gap-2">
      {items.map((m, i) => (
        <div key={i} className="flex flex-col gap-1 p-2.5 rounded bg-surface/50 border border-border/50">
          <div className="flex items-baseline justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-white text-xs">{m.name || 'Management Change'}</span>
              {m.role && <span className="chip chip-mgmt text-[9px]">{m.role}</span>}
            </div>
            {m.effective_date && (
              <span className="text-[10px] text-muted font-mono shrink-0">
                Eff: {m.effective_date}
              </span>
            )}
          </div>

          {m.profile_text && (
            <div className="mt-1 text-[11px] text-white/85 leading-relaxed bg-black/20 p-2.5 rounded border border-border/30">
              <span className="text-[9px] font-mono text-accent uppercase tracking-wider block mb-1">
                from the company filing:
              </span>
              <p className="line-clamp-4">{m.profile_text}</p>
            </div>
          )}

          {m.source_url && m.source_url !== 'unavailable' && (
            <div className="flex justify-end mt-1">
              <a
                href={m.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-[10px] text-accent hover:underline font-mono"
              >
                <span>Filing PDF{m.page_number ? ` (p.${m.page_number})` : ''}</span>
                <ExternalLink size={10} />
              </a>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function FilingRow({ filing }) {
  // snapshot uses: desc, attachment_url, seq_id, category, attachment_text
  const desc = filing.desc || filing.sm_name || '—'
  const url  = filing.attachment_url || filing.attchmntFile
  const cat  = filing.category
  const catM = cat ? categoryMeta(cat) : null
  return (
    <div className="flex items-center gap-2 px-4 py-2.5 text-xs">
      {url && <Paperclip size={10} className="text-muted shrink-0" />}
      {catM && <span className={clsx('chip text-[9px]', catM.chip)}>{catM.label}</span>}
      <span className="flex-1 text-muted line-clamp-1">{desc}</span>
      {url && (
        <a
          href={url.startsWith('http') ? url : `https://www.nseindia.com${url}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent hover:text-indigo-300 transition-colors"
        >
          <ExternalLink size={11} />
        </a>
      )}
    </div>
  )
}
