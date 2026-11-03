import { useState } from 'react'
import { Search, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

const DEMO_TICKERS = ['DIXON', 'KAYNES', 'M&M', 'ASTRAL']

export default function ResearchTab() {
  const [query, setQuery]     = useState('')
  const [submitted, setSubmitted] = useState('')
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  async function runSearch(ticker) {
    const sym = ticker.trim().toUpperCase()
    if (!sym) return
    setSubmitted(sym)
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const r = await fetch(`/api/research/${encodeURIComponent(sym)}`)
      const json = await r.json()
      if (json.status === 'unavailable_from_cloud') {
        setError('Live research is unavailable in the deployed demo (cloud IPs are blocked by data sources). Run the pipeline locally to generate a snapshot for this ticker.')
      } else if (!r.ok) {
        setError(json.detail || `Server error ${r.status}`)
      } else {
        setResult(json)
      }
    } catch (e) {
      setError('API unreachable. In demo mode, only pre-cached tickers are available. ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  function onSubmit(e) {
    e.preventDefault()
    runSearch(query)
  }

  return (
    <div className="flex flex-col px-4 pt-5 gap-5">
      {/* Search bar */}
      <form onSubmit={onSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value.toUpperCase())}
            placeholder="NSE ticker (e.g. DIXON)"
            className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-card border border-border text-sm text-white placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-4 py-2.5 rounded-lg bg-accent text-white text-sm font-medium disabled:opacity-50 transition-opacity"
        >
          {loading ? '…' : 'Go'}
        </button>
      </form>

      {/* Demo chips */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-muted self-center">Pre-cached:</span>
        {DEMO_TICKERS.map(t => (
          <button
            key={t}
            onClick={() => { setQuery(t); runSearch(t) }}
            className="chip chip-call hover:bg-blue-500/30 transition-colors cursor-pointer"
          >
            {t}
          </button>
        ))}
      </div>

      {/* Cloud warning */}
      <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-warning/10 border border-warning/30 text-xs text-warning">
        <AlertCircle size={13} className="shrink-0 mt-0.5" />
        <span>
          Deployed on Render free tier — first request may take ~60s (cold start).
          Research data comes from pre-cached snapshots only;
          live NSE/Screener lookups are blocked on cloud servers.
        </span>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 px-3 py-3 rounded-lg bg-negative/10 border border-negative/30 text-xs text-negative">
          <AlertCircle size={13} className="shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="flex flex-col gap-3 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 rounded-xl bg-card border border-border" />
          ))}
        </div>
      )}

      {/* Result */}
      {result && <ResearchResult data={result} />}

      {/* Empty state */}
      {!loading && !result && !error && (
        <div className="text-center text-muted text-sm py-12">
          Search any NSE ticker. Research is grounded only in annual reports + concall transcripts.
        </div>
      )}
    </div>
  )
}

function ResearchResult({ data }) {
  // Full research result rendering — wired up in Step 6
  // For now show a structured placeholder
  return (
    <div className="flex flex-col gap-4">
      {/* Header */}
      <div className="rounded-xl bg-card border border-border p-4">
        <div className="flex items-baseline justify-between">
          <h2 className="font-bold text-lg text-white">{data.symbol || data.ticker}</h2>
          {data.as_of && <span className="text-xs text-muted font-mono">as of {data.as_of}</span>}
        </div>
        {data.company_name && <p className="text-sm text-muted mt-0.5">{data.company_name}</p>}
        {data.sector && <p className="text-xs text-muted">{data.sector}</p>}
      </div>

      {/* Promised vs Delivered hero */}
      {data.promised_vs_delivered ? (
        <PromisedDelivered matrix={data.promised_vs_delivered} />
      ) : (
        <div className="rounded-xl bg-card border border-border p-4">
          <h3 className="text-xs font-semibold uppercase tracking-widest text-muted mb-2">Promised vs. Delivered</h3>
          <p className="text-sm text-muted italic">Extraction pending (Step 6)</p>
        </div>
      )}

      {/* Financial trajectory */}
      {data.financials && <FinancialSection financials={data.financials} />}

      {/* Bull / Bear */}
      {(data.bull_case || data.bear_case) && (
        <div className="grid grid-cols-2 gap-3">
          {data.bull_case && (
            <div className="rounded-xl bg-positive/10 border border-positive/20 p-3">
              <h3 className="text-[10px] font-semibold uppercase tracking-widest text-positive mb-2">Bull</h3>
              <ul className="text-xs text-positive/80 flex flex-col gap-1">
                {data.bull_case.map((p, i) => <li key={i}>• {p}</li>)}
              </ul>
            </div>
          )}
          {data.bear_case && (
            <div className="rounded-xl bg-negative/10 border border-negative/20 p-3">
              <h3 className="text-[10px] font-semibold uppercase tracking-widest text-negative mb-2">Bear</h3>
              <ul className="text-xs text-negative/80 flex flex-col gap-1">
                {data.bear_case.map((p, i) => <li key={i}>• {p}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Citations */}
      {data.citations?.length > 0 && (
        <div className="rounded-xl bg-card border border-border p-4">
          <h3 className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-2">Sources</h3>
          <div className="flex flex-col gap-1">
            {data.citations.map((c, i) => (
              <div key={i} className="text-xs text-muted flex items-center gap-2">
                <span className="chip chip-call text-[9px]">{c.doc}</span>
                <span className="italic line-clamp-1 flex-1">"{c.excerpt}"</span>
                {c.page && <span className="font-mono text-[9px] shrink-0">p.{c.page}</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function PromisedDelivered({ matrix }) {
  const VERDICT_STYLE = {
    Beat:    'bg-positive/20 text-positive border-positive/30',
    Met:     'bg-blue-500/20 text-blue-300 border-blue-500/30',
    Missed:  'bg-negative/20 text-negative border-negative/30',
    Pivoted: 'bg-warning/20 text-warning border-warning/30',
  }

  return (
    <div className="rounded-xl bg-card border border-border p-4">
      <h3 className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-3">Promised vs. Delivered</h3>
      <div className="flex flex-col gap-3">
        {matrix.map((row, i) => (
          <div key={i} className={clsx('border rounded-lg p-3 text-xs', VERDICT_STYLE[row.verdict] || 'border-border')}>
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold">{row.period}</span>
              <span className="chip text-[9px] border">{row.verdict}</span>
            </div>
            <p className="text-white/70 italic">"{row.promise}"</p>
            <p className="mt-1 text-white/50">→ {row.outcome}</p>
            {row.citation && (
              <p className="mt-1 font-mono text-[9px] opacity-60">[{row.citation}]</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function FinancialSection({ financials }) {
  return (
    <div className="rounded-xl bg-card border border-border p-4">
      <h3 className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-3">Financial Trajectory</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-muted">
              <th className="text-left pb-2 font-medium">Period</th>
              <th className="text-right pb-2 font-medium">Revenue</th>
              <th className="text-right pb-2 font-medium">PAT</th>
              <th className="text-right pb-2 font-medium">Margin</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {financials.map((row, i) => (
              <tr key={i}>
                <td className="py-1.5 text-muted">{row.period}</td>
                <td className="py-1.5 text-right font-mono text-white">{row.revenue ?? '—'}</td>
                <td className="py-1.5 text-right font-mono text-white">{row.pat ?? '—'}</td>
                <td className="py-1.5 text-right font-mono text-muted">{row.margin ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

