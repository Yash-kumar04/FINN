import { useState, useEffect, useMemo } from 'react'
import {
  Search,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  TrendingUp,
  TrendingDown,
  Building2,
  Scale,
  DollarSign,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  X,
  FileText
} from 'lucide-react'
import clsx from 'clsx'

const DEMO_TICKERS = ['DIXON', 'PIDILITIND', 'KAYNES', 'M&M', 'ASTRAL', 'INFY']

export default function ResearchTab() {
  const [query, setQuery] = useState('DIXON')
  const [selectedTicker, setSelectedTicker] = useState('DIXON')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [statusMessage, setStatusMessage] = useState(null)
  const [activeCitation, setActiveCitation] = useState(null)

  // Fetch research data
  async function loadResearch(ticker) {
    const sym = ticker.trim().toUpperCase()
    if (!sym) return
    setSelectedTicker(sym)
    setLoading(true)
    setError(null)
    setStatusMessage(null)

    try {
      // First try local backend API
      let res = await fetch(`/api/research/${encodeURIComponent(sym)}`).catch(() => null)
      if (res && res.ok) {
        const json = await res.json()
        if (json.status === 'processing') {
          setStatusMessage('Pipeline is currently processing this ticker. Please check back shortly.')
          setData(null)
          return
        }
        if (json.status === 'unavailable') {
          setError(json.reason || 'Data sources blocked or unavailable.')
          setData(null)
          return
        }
        setData(json)
        return
      }

      // Fallback to static public snapshot
      const staticRes = await fetch(`/data/research/${encodeURIComponent(sym)}.json`)
      if (staticRes.ok) {
        const staticJson = await staticRes.json()
        setData(staticJson)
        return
      }

      // If neither is available
      setError(`No pre-computed research dossier available for ${sym}. Primary research requires running the local pipeline to comply with cloud IP restrictions.`)
      setData(null)
    } catch (err) {
      setError(`Failed to load research for ${sym}: ${err.message}`)
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  // Load default on mount
  useEffect(() => {
    loadResearch('DIXON')
  }, [])

  function handleSubmit(e) {
    e.preventDefault()
    if (query.trim()) {
      loadResearch(query)
    }
  }

  return (
    <div className="flex flex-col px-4 pt-4 pb-12 gap-5 max-w-lg mx-auto">
      {/* Search Header */}
      <div className="flex flex-col gap-2.5">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value.toUpperCase())}
              placeholder="NSE ticker (e.g. DIXON)"
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-card border border-border text-xs text-white placeholder:text-muted focus:outline-none focus:border-accent transition-colors uppercase font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2 rounded-lg bg-accent text-white text-xs font-semibold hover:bg-accent/80 disabled:opacity-50 transition-opacity"
          >
            {loading ? '…' : 'Research'}
          </button>
        </form>

        {/* Demo Tickers Chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] text-muted shrink-0">Demo:</span>
          {DEMO_TICKERS.map(t => (
            <button
              key={t}
              onClick={() => {
                setQuery(t)
                loadResearch(t)
              }}
              className={clsx(
                'px-2.5 py-0.5 rounded-full text-xs font-mono font-medium transition-colors cursor-pointer border',
                selectedTicker === t
                  ? 'bg-accent/20 text-accent border-accent/40'
                  : 'bg-card text-muted hover:text-white border-border'
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Status or Error Message */}
      {statusMessage && (
        <div className="p-3 rounded-lg bg-accent/10 border border-accent/30 text-accent text-xs">
          {statusMessage}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-negative/10 border border-negative/30 text-negative text-xs flex items-start gap-2">
          <AlertTriangle size={14} className="shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="flex flex-col gap-3 animate-pulse">
          <div className="h-28 rounded-xl bg-card border border-border" />
          <div className="h-64 rounded-xl bg-card border border-border" />
          <div className="h-44 rounded-xl bg-card border border-border" />
        </div>
      )}

      {/* Research Content */}
      {!loading && data && (
        <ResearchDossier
          data={data}
          onOpenCitation={citation => setActiveCitation(citation)}
        />
      )}

      {/* Citation Detail Modal */}
      {activeCitation && (
        <CitationModal
          citation={activeCitation}
          onClose={() => setActiveCitation(null)}
        />
      )}
    </div>
  )
}

function ResearchDossier({ data, onOpenCitation }) {
  const [filterVerdict, setFilterVerdict] = useState('ALL')
  const [showAllPromises, setShowAllPromises] = useState(false)

  // Map of fact_id to fact details for quick modal resolution
  const factMap = useMemo(() => {
    const map = new Map()
    if (data.promised_vs_delivered) {
      data.promised_vs_delivered.forEach(p => {
        if (p.fact_id) map.set(p.fact_id, p)
      })
    }
    if (data.annual_report_facts) {
      data.annual_report_facts.forEach(f => {
        if (f.fact_id) map.set(f.fact_id, f)
      })
    }
    return map
  }, [data])

  const promises = data.promised_vs_delivered || []

  // Count verdicts
  const verdictCounts = useMemo(() => {
    const counts = { Met: 0, Beat: 0, Missed: 0, Unclear: 0 }
    promises.forEach(p => {
      if (counts[p.verdict] !== undefined) counts[p.verdict]++
      else counts.Unclear++
    })
    return counts
  }, [promises])

  // Filtered scorecard rows
  const filteredPromises = useMemo(() => {
    let list = promises
    if (filterVerdict !== 'ALL') {
      list = list.filter(p => p.verdict === filterVerdict)
    }
    return showAllPromises ? list : list.slice(0, 5)
  }, [promises, filterVerdict, showAllPromises])

  return (
    <div className="flex flex-col gap-5">
      {/* Company Title Card */}
      <div className="p-4 rounded-xl bg-card border border-border">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">{data.ticker}</h1>
              <span className="chip chip-results text-[10px] font-mono">Q2 FY27 Verified</span>
            </div>
            <p className="text-xs text-muted mt-0.5">{data.company_name}</p>
            <p className="text-[11px] text-muted/80">{data.sector}</p>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-muted font-mono block">Data as of {data.as_of}</span>
            <span className="text-[9px] text-muted/60 font-mono block">Audited Primary Filings</span>
          </div>
        </div>

        {/* Audit Callout Pill */}
        <div className="mt-3 pt-3 border-t border-border/60 flex items-center justify-between text-[11px] text-muted">
          <span className="flex items-center gap-1.5 text-positive">
            <CheckCircle2 size={12} />
            <span>Strict Metric Alignment Enforced</span>
          </span>
          <span className="font-mono text-[10px] text-muted/70">
            {promises.length} concall promises · {data.annual_report_facts?.length || 0} AR facts
          </span>
        </div>
      </div>

      {/* SECTION 1: HERO PROMISED VS DELIVERED SCORECARD */}
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-4 rounded-sm bg-accent" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-white">
              Promised vs. Delivered Scorecard
            </h2>
          </div>
          <span className="text-[10px] text-muted font-mono">5 Quarters Analyzed</span>
        </div>

        {/* Verdict Count Cards */}
        <div className="grid grid-cols-4 gap-2">
          <VerdictCard
            label="Met"
            count={verdictCounts.Met}
            color="border-blue-500/30 bg-blue-500/10 text-blue-400"
            active={filterVerdict === 'Met'}
            onClick={() => setFilterVerdict(filterVerdict === 'Met' ? 'ALL' : 'Met')}
          />
          <VerdictCard
            label="Beat"
            count={verdictCounts.Beat}
            color="border-positive/30 bg-positive/10 text-positive"
            active={filterVerdict === 'Beat'}
            onClick={() => setFilterVerdict(filterVerdict === 'Beat' ? 'ALL' : 'Beat')}
          />
          <VerdictCard
            label="Missed"
            count={verdictCounts.Missed}
            color="border-negative/30 bg-negative/10 text-negative"
            active={filterVerdict === 'Missed'}
            onClick={() => setFilterVerdict(filterVerdict === 'Missed' ? 'ALL' : 'Missed')}
          />
          <VerdictCard
            label="Unclear"
            count={verdictCounts.Unclear}
            color="border-warning/30 bg-warning/10 text-warning"
            active={filterVerdict === 'Unclear'}
            onClick={() => setFilterVerdict(filterVerdict === 'Unclear' ? 'ALL' : 'Unclear')}
          />
        </div>

        {/* Filter Reset pill if filter active */}
        {filterVerdict !== 'ALL' && (
          <div className="flex items-center justify-between px-1 text-[11px] text-muted">
            <span>Filtered by: <strong className="text-white">{filterVerdict}</strong></span>
            <button
              onClick={() => setFilterVerdict('ALL')}
              className="text-accent underline text-[10px] cursor-pointer"
            >
              Show All ({promises.length})
            </button>
          </div>
        )}

        {/* Promise Cards List */}
        {promises.length === 0 ? (
          <div className="p-5 rounded-xl bg-card border border-border flex flex-col items-center justify-center text-center gap-2 py-8">
            <FileText size={24} className="text-muted/60" />
            <p className="text-xs font-semibold text-white">No numeric guidance in prepared remarks</p>
            <p className="text-[11px] text-muted max-w-sm">
              Management reviewed historical performance only and did not state checkable numeric guidance (growth %, margin %, revenue, capex) in prepared remarks across concalls.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {filteredPromises.map((item, idx) => (
              <PromiseCard
                key={item.fact_id || idx}
                item={item}
                onOpenCitation={() => onOpenCitation(item)}
              />
            ))}
          </div>
        )}

        {/* Show More / Show Less Button */}
        {promises.length > 5 && (
          <button
            onClick={() => setShowAllPromises(!showAllPromises)}
            className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-card hover:bg-card/80 border border-border text-xs text-muted hover:text-white transition-colors"
          >
            {showAllPromises ? (
              <>
                <ChevronUp size={13} />
                <span>Show Top 5 Only</span>
              </>
            ) : (
              <>
                <ChevronDown size={13} />
                <span>Show All {promises.length} Promises</span>
              </>
            )}
          </button>
        )}

        {/* Metric Alignment Rule Note */}
        <div className="p-3 rounded-lg bg-card/60 border border-border text-[11px] text-muted flex items-start gap-2">
          <HelpCircle size={14} className="shrink-0 text-accent mt-0.5" />
          <div className="flex flex-col gap-0.5">
            <span className="font-semibold text-white/90">Strict Metric Alignment Rule:</span>
            <span>
              Verdicts compare like-for-like metrics only (revenue vs revenue, volume vs volume). Volume promises with only revenue figures reported are marked <strong className="text-warning">Unclear</strong> because top-line growth conflates physical units with price mix.
            </span>
          </div>
        </div>
      </section>

      {/* SECTION 2: ANNUAL REPORT & FINANCIAL DEEP DIVE */}
      <section className="flex flex-col gap-3 pt-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-4 rounded-sm bg-accent" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-white">
              Annual Report & Fundamental Reality
            </h2>
          </div>
          <span className="text-[10px] text-muted font-mono">{data.as_of ? `As of ${data.as_of}` : 'FY 2025-26 Report'}</span>
        </div>

        {/* Audited Annual Report Facts & Provenance */}
        {data.annual_report_facts && data.annual_report_facts.length > 0 && (
          <div className="p-4 rounded-xl bg-card border border-border flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs font-semibold text-white">
              <div className="flex items-center gap-2">
                <FileText size={14} className="text-accent" />
                <span>Audited Annual Report Facts ({data.annual_report_facts.length} Verified)</span>
              </div>
              <span className="text-[10px] text-muted font-mono">Primary Source</span>
            </div>
            <div className="flex flex-col gap-2">
              {data.annual_report_facts.map((fact, idx) => (
                <div key={fact.fact_id || idx} className="p-2.5 rounded-lg bg-surface border border-border/60 flex flex-col gap-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white/90">{fact.metric}</span>
                    <button
                      onClick={() => onOpenCitation(fact)}
                      className="text-[10px] text-accent hover:underline font-mono"
                    >
                      [p.{fact.page || 1}]
                    </button>
                  </div>
                  <p className="text-[11px] text-muted leading-relaxed">
                    {fact.statement}
                  </p>
                  {fact.value && (
                    <div className="text-[10px] font-mono text-positive/90 mt-0.5">
                      Extracted: <span className="font-semibold">{fact.value}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {data.ticker === 'DIXON' && (
          <>
            {/* Business Snapshot & Segment Mix */}
        <div className="p-4 rounded-xl bg-card border border-border flex flex-col gap-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-white">
            <Building2 size={14} className="text-accent" />
            <span>Manufacturing Footprint & Revenue Mix</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-lg bg-surface border border-border/70">
              <span className="text-[10px] text-muted block">Facilities</span>
              <span className="font-semibold text-white">23 Units (3.2M sq. ft.)</span>
            </div>
            <div className="p-2.5 rounded-lg bg-surface border border-border/70">
              <span className="text-[10px] text-muted block">R&D & Engineering</span>
              <span className="font-semibold text-white">3 Dedicated Centers</span>
            </div>
          </div>

          {/* Segmental Breakdown Bars */}
          <div className="flex flex-col gap-2 pt-1">
            <span className="text-[11px] font-medium text-muted">Revenue Breakdown (FY26):</span>
            
            <SegmentBar
              name="Mobile Phones & Other EMS"
              amount="₹44,257 Cr"
              pct={90.6}
              color="bg-accent"
              onCite={() => onOpenCitation(factMap.get('fact_ar_biz_4'))}
            />
            <SegmentBar
              name="Consumer Electronics & Refrigerators"
              amount="₹2,892 Cr"
              pct={5.9}
              color="bg-blue-400"
              onCite={() => onOpenCitation(factMap.get('fact_ar_biz_5'))}
            />
            <SegmentBar
              name="Lighting Products"
              amount="₹1,222 Cr"
              pct={2.5}
              color="bg-amber-400"
              onCite={() => onOpenCitation(factMap.get('fact_ar_biz_4'))}
            />
            <SegmentBar
              name="Home Appliances (Washing Machines)"
              amount="₹448 Cr"
              pct={0.9}
              color="bg-emerald-400"
              onCite={() => onOpenCitation(factMap.get('fact_ar_biz_4'))}
            />
          </div>
        </div>

        {/* 5-Year Trajectory & Financial Snapshot */}
        <div className="p-4 rounded-xl bg-card border border-border flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs font-semibold text-white">
            <div className="flex items-center gap-2">
              <TrendingUp size={14} className="text-positive" />
              <span>5-Year Growth Trajectory</span>
            </div>
            <button
              onClick={() => onOpenCitation(factMap.get('fact_ar_traj_1'))}
              className="text-[10px] text-accent hover:underline font-mono"
            >
              [p.106]
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border text-muted text-[10px] uppercase">
                  <th className="text-left pb-2 font-medium">Metric</th>
                  <th className="text-right pb-2 font-medium">FY22</th>
                  <th className="text-right pb-2 font-medium">FY26</th>
                  <th className="text-right pb-2 font-medium">4-Yr CAGR</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40 font-mono">
                <tr>
                  <td className="py-2 text-white/80 font-sans">Revenue</td>
                  <td className="py-2 text-right text-muted">₹10,697 Cr</td>
                  <td className="py-2 text-right text-white font-semibold">₹48,873 Cr</td>
                  <td className="py-2 text-right text-positive">+46.1%</td>
                </tr>
                <tr>
                  <td className="py-2 text-white/80 font-sans">EBITDA</td>
                  <td className="py-2 text-right text-muted">₹405 Cr</td>
                  <td className="py-2 text-right text-white font-semibold">₹2,580 Cr</td>
                  <td className="py-2 text-right text-positive">+58.9%</td>
                </tr>
                <tr>
                  <td className="py-2 text-white/80 font-sans">PAT</td>
                  <td className="py-2 text-right text-muted">₹190 Cr</td>
                  <td className="py-2 text-right text-white font-semibold">₹1,644 Cr</td>
                  <td className="py-2 text-right text-positive">+71.5%</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Key Return Ratios */}
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border/60">
            <div className="p-2 rounded-lg bg-surface flex items-center justify-between">
              <span className="text-[11px] text-muted">RoCE</span>
              <span className="text-xs font-mono font-bold text-positive">44.8%</span>
            </div>
            <div className="p-2 rounded-lg bg-surface flex items-center justify-between">
              <span className="text-[11px] text-muted">RoE</span>
              <span className="text-xs font-mono font-bold text-positive">28.1%</span>
            </div>
          </div>
        </div>

        {/* Balance Sheet & Working Capital Efficiency */}
        <div className="p-4 rounded-xl bg-card border border-border flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs font-semibold text-white">
            <div className="flex items-center gap-2">
              <Scale size={14} className="text-accent" />
              <span>Balance Sheet & Working Capital Cycle</span>
            </div>
            <button
              onClick={() => onOpenCitation(factMap.get('fact_ar_bs_2'))}
              className="text-[10px] text-accent hover:underline font-mono"
            >
              [p.106, 405]
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-lg bg-surface border border-border/70">
              <span className="text-[10px] text-muted block">Net Debt</span>
              <span className="font-semibold text-positive">-₹773 Cr (Surplus)</span>
            </div>
            <div className="p-2.5 rounded-lg bg-surface border border-border/70">
              <span className="text-[10px] text-muted block">Current Ratio</span>
              <span className="font-semibold text-white font-mono">1.37x</span>
            </div>
          </div>

          {/* Days */}
          <div className="grid grid-cols-3 gap-2 pt-1 text-center font-mono text-xs">
            <div className="p-2 rounded-lg bg-surface">
              <span className="text-[10px] text-muted block font-sans">Inventory</span>
              <span className="text-white font-semibold">48.4 days</span>
            </div>
            <div className="p-2 rounded-lg bg-surface">
              <span className="text-[10px] text-muted block font-sans">Debtors</span>
              <span className="text-white font-semibold">54.0 days</span>
            </div>
            <div className="p-2 rounded-lg bg-surface">
              <span className="text-[10px] text-muted block font-sans">Payables</span>
              <span className="text-white font-semibold">75.6 days</span>
            </div>
          </div>
        </div>

        {/* Cash Conversion Quality */}
        <div className="p-4 rounded-xl bg-card border border-border flex flex-col gap-2.5">
          <div className="flex items-center justify-between text-xs font-semibold text-white">
            <div className="flex items-center gap-2">
              <DollarSign size={14} className="text-positive" />
              <span>Cash Flow Quality (108% Conversion)</span>
            </div>
            <button
              onClick={() => onOpenCitation(factMap.get('fact_ar_cash_1'))}
              className="text-[10px] text-accent hover:underline font-mono"
            >
              [p.420]
            </button>
          </div>

          <div className="p-3 rounded-lg bg-positive/10 border border-positive/30 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-positive/80 uppercase font-bold tracking-wider block">
                Cash from Operations
              </span>
              <span className="text-base font-bold text-white font-mono">₹1,782 Cr</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-positive/80 uppercase font-bold tracking-wider block">
                Reported PAT
              </span>
              <span className="text-base font-bold text-white font-mono">₹1,644 Cr</span>
            </div>
          </div>
          <p className="text-[11px] text-muted">
            Operating cash conversion exceeded 108.4% of reported PAT, generating ₹714.8 Cr of Free Cash Flow after ₹1,067.5 Cr capex.
          </p>
        </div>

        {/* Contingent Liabilities & Legal Disclosures */}
        <div className="p-4 rounded-xl bg-card border border-border flex flex-col gap-2.5">
          <div className="flex items-center justify-between text-xs font-semibold text-white">
            <div className="flex items-center gap-2">
              <ShieldAlert size={14} className="text-warning" />
              <span>Contingent Liabilities & DRI Tax Inquiries</span>
            </div>
            <button
              onClick={() => onOpenCitation(factMap.get('fact_ar_cont_1'))}
              className="text-[10px] text-accent hover:underline font-mono"
            >
              [p.474]
            </button>
          </div>

          <div className="flex flex-col gap-1.5 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-border/50">
              <span className="text-muted">Disputed Customs & Excise</span>
              <span className="font-mono text-warning font-semibold">₹398.4 Cr</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50">
              <span className="text-muted">Direct Tax & GST Claims</span>
              <span className="font-mono text-white font-semibold">₹118.0 Cr</span>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-muted">Supplier Guarantees & LCs</span>
              <span className="font-mono text-white font-semibold">₹1,231.2 Cr</span>
            </div>
          </div>
        </div>
          </>
        )}
      </section>

      {/* SECTION 3: NARRATIVE VS NUMBERS DIVERGENCES */}
      {data.narrative_vs_numbers && data.narrative_vs_numbers.length > 0 && (
        <section className="flex flex-col gap-3 pt-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-4 rounded-sm bg-accent" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">
                Narrative vs. Numbers Reality Check
              </h2>
            </div>
            <span className="text-[10px] text-muted font-mono">{data.narrative_vs_numbers.length} Checks</span>
          </div>

          <div className="flex flex-col gap-3">
            {data.narrative_vs_numbers.map((item, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-card border border-border flex flex-col gap-2.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-white">{item.topic}</h3>
                  <span
                    className={clsx(
                      'text-[9px] px-2 py-0.5 rounded-full font-semibold border',
                      item.divergence_type === 'Agrees'
                        ? 'bg-positive/20 text-positive border-positive/30'
                        : item.divergence_type === 'Under Observation'
                        ? 'bg-warning/20 text-warning border-warning/30'
                        : 'bg-negative/20 text-negative border-negative/30'
                    )}
                  >
                    {item.divergence_type}
                  </span>
                </div>

                <div className="flex flex-col gap-1.5 text-xs">
                  <div className="p-2.5 rounded-lg bg-surface border border-border/60">
                    <span className="text-[10px] uppercase font-bold text-muted block">Management Narrative</span>
                    <p className="text-white/80 mt-0.5 italic">"{item.management_narrative}"</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface border border-border/60">
                    <span className="text-[10px] uppercase font-bold text-muted block">Reported Numbers</span>
                    <p className="text-white/90 mt-0.5">{item.reported_numbers}</p>
                  </div>
                </div>

                <p className="text-[11px] text-muted leading-relaxed">
                  {item.analysis}
                </p>

                {item.cited_fact_ids && item.cited_fact_ids.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap pt-1 border-t border-border/50">
                    <span className="text-[10px] text-muted">Cited facts:</span>
                    {item.cited_fact_ids.map(fid => {
                      const f = factMap.get(fid)
                      return (
                        <button
                          key={fid}
                          onClick={() => f && onOpenCitation(f)}
                          className="chip chip-other text-[9px] font-mono hover:text-white cursor-pointer"
                        >
                          [{f?.metric || fid}]
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* SECTION 4: SYNTHESIS BULL VS BEAR CASE */}
      {(data.bull_case || data.bear_case) && (
        <section className="flex flex-col gap-3 pt-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-4 rounded-sm bg-accent" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">
                Bull vs. Bear Thesis
              </h2>
            </div>
            <span className="text-[10px] text-muted font-mono">Audited Claims Only</span>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {/* Bull Case */}
            {data.bull_case && (
              <div className="p-4 rounded-xl bg-positive/10 border border-positive/30 flex flex-col gap-3">
                <div className="flex items-center gap-2 text-positive font-bold text-xs uppercase tracking-wider">
                  <TrendingUp size={14} />
                  <span>The Bull Case (3 Pillars)</span>
                </div>
                <div className="flex flex-col gap-2.5">
                  {data.bull_case.map((item, idx) => (
                    <div key={idx} className="flex flex-col gap-1 text-xs">
                      <div className="flex items-baseline justify-between">
                        <strong className="text-white">{item.title}</strong>
                      </div>
                      <p className="text-positive/90 text-[11px] leading-relaxed">
                        {item.argument}
                      </p>
                      {item.cited_fact_ids && (
                        <div className="flex gap-1 flex-wrap mt-0.5">
                          {item.cited_fact_ids.map(fid => {
                            const f = factMap.get(fid)
                            return (
                              <button
                                key={fid}
                                onClick={() => f && onOpenCitation(f)}
                                className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-positive/20 text-positive hover:underline cursor-pointer"
                              >
                                [{f?.page ? `p.${f.page}` : fid}]
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bear Case */}
            {data.bear_case && (
              <div className="p-4 rounded-xl bg-negative/10 border border-negative/30 flex flex-col gap-3">
                <div className="flex items-center gap-2 text-negative font-bold text-xs uppercase tracking-wider">
                  <TrendingDown size={14} />
                  <span>The Bear Case (3 Vulnerabilities)</span>
                </div>
                <div className="flex flex-col gap-2.5">
                  {data.bear_case.map((item, idx) => (
                    <div key={idx} className="flex flex-col gap-1 text-xs">
                      <div className="flex items-baseline justify-between">
                        <strong className="text-white">{item.title}</strong>
                      </div>
                      <p className="text-negative/90 text-[11px] leading-relaxed">
                        {item.argument}
                      </p>
                      {item.cited_fact_ids && (
                        <div className="flex gap-1 flex-wrap mt-0.5">
                          {item.cited_fact_ids.map(fid => {
                            const f = factMap.get(fid)
                            return (
                              <button
                                key={fid}
                                onClick={() => f && onOpenCitation(f)}
                                className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-negative/20 text-negative hover:underline cursor-pointer"
                              >
                                [{f?.page ? `p.${f.page}` : fid}]
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  )
}

function VerdictCard({ label, count, color, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'p-2.5 rounded-xl border flex flex-col items-center justify-center transition-all cursor-pointer',
        color,
        active && 'ring-2 ring-accent scale-105'
      )}
    >
      <span className="text-[10px] uppercase font-bold tracking-wider">{label}</span>
      <span className="text-lg font-mono font-extrabold mt-0.5">{count}</span>
    </button>
  )
}

function PromiseCard({ item, onOpenCitation }) {
  const VERDICT_BADGE = {
    Beat: 'bg-positive/20 text-positive border-positive/30',
    Met: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    Missed: 'bg-negative/20 text-negative border-negative/30',
    Unclear: 'bg-warning/20 text-warning border-warning/30'
  }

  return (
    <div className="p-3.5 rounded-xl bg-card border border-border flex flex-col gap-2 text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="font-semibold text-white">{item.period || item.call_date}</span>
          <span className="text-[10px] text-muted font-mono">({item.transcript_period || item.call_date})</span>
        </div>
        <span className={clsx('chip text-[10px] border font-bold', VERDICT_BADGE[item.verdict] || 'border-border text-muted')}>
          {item.verdict}
        </span>
      </div>

      {/* Promised */}
      <div className="flex flex-col gap-0.5">
        <span className="text-[10px] uppercase font-bold text-muted">Promised:</span>
        <p className="text-white font-medium">{item.promised || item.promise}</p>
      </div>

      {/* Delivered */}
      <div className="flex flex-col gap-0.5">
        <span className="text-[10px] uppercase font-bold text-muted">Delivered:</span>
        <p className="text-white/90">
          <span className="font-semibold">{item.delivered_figure || item.delivered}</span>
          {item.delivered_source && (
            <span className="text-[10px] text-muted block mt-0.5 font-mono">
              Source: {item.delivered_source}
            </span>
          )}
        </p>
      </div>

      {/* Exact Quote */}
      <div className="p-2 rounded bg-surface border border-border/60 text-[11px] italic text-white/70">
        "{item.quote?.replace(/\n/g, ' ')}"
      </div>

      {/* Card Footer: Citation Link */}
      <div className="flex items-center justify-between pt-1 border-t border-border/50 text-[10px]">
        <button
          onClick={onOpenCitation}
          className="text-accent hover:underline flex items-center gap-1 cursor-pointer font-mono"
        >
          <FileText size={11} />
          <span>Page {item.page} Citation & Details</span>
        </button>

        {item.source_url && (
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted hover:text-white flex items-center gap-1 font-mono"
          >
            <span>Primary PDF</span>
            <ExternalLink size={10} />
          </a>
        )}
      </div>
    </div>
  )
}

function SegmentBar({ name, amount, pct, color, onCite }) {
  return (
    <div className="flex flex-col gap-1 text-xs">
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-white/80">{name}</span>
        <div className="flex items-center gap-1.5 font-mono">
          <span className="text-white font-semibold">{amount}</span>
          <span className="text-muted">({pct}%)</span>
          {onCite && (
            <button
              onClick={onCite}
              className="text-[9px] text-accent hover:underline cursor-pointer"
            >
              [p.106]
            </button>
          )}
        </div>
      </div>
      <div className="w-full h-1.5 rounded-full bg-surface overflow-hidden">
        <div className={clsx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function CitationModal({ citation, onClose }) {
  if (!citation) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md rounded-2xl bg-card border border-border p-5 flex flex-col gap-4 shadow-2xl">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="chip chip-results text-[10px] font-mono">
                {citation.fact_id || 'AUDITED CITATION'}
              </span>
              {citation.page && (
                <span className="chip chip-other text-[10px] font-mono">
                  Page {citation.page}
                </span>
              )}
            </div>
            <h3 className="text-sm font-bold text-white mt-1.5">
              {citation.metric || citation.topic || 'Primary Filing Citation'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-surface text-muted hover:text-white transition-colors cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Statement / Quote */}
        <div className="p-3 rounded-xl bg-surface border border-border text-xs flex flex-col gap-1">
          <span className="text-[10px] uppercase font-bold text-muted">Audited Primary Statement</span>
          <p className="text-white/90 leading-relaxed italic">
            "{citation.statement || citation.quote || citation.argument || 'N/A'}"
          </p>
        </div>

        {/* Extra metadata */}
        <div className="flex flex-col gap-1 text-[11px] text-muted">
          {citation.call_date && (
            <div className="flex justify-between py-0.5 border-b border-border/40">
              <span>Event Date:</span>
              <span className="text-white font-mono">{citation.call_date}</span>
            </div>
          )}
          {citation.value && (
            <div className="flex justify-between py-0.5 border-b border-border/40">
              <span>Extracted Value:</span>
              <span className="text-white font-mono font-semibold">{citation.value}</span>
            </div>
          )}
          {citation.section && (
            <div className="flex justify-between py-0.5 border-b border-border/40">
              <span>Section:</span>
              <span className="text-white font-mono">{citation.section}</span>
            </div>
          )}
        </div>

        {/* Primary Link Button */}
        {citation.source_url ? (
          <a
            href={citation.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-accent hover:bg-accent/80 text-white text-xs font-semibold transition-colors"
          >
            <span>Open Primary Filing PDF (Page {citation.page || 1})</span>
            <ExternalLink size={13} />
          </a>
        ) : (
          <div className="text-center text-[10px] text-muted italic">
            Primary URL not provided for this row
          </div>
        )}
      </div>
    </div>
  )
}
