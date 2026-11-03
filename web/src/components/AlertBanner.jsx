import { useState } from 'react'
import { TrendingUp, TrendingDown, Flame, FileText, ArrowRight, X, ExternalLink, Sparkles } from 'lucide-react'
import clsx from 'clsx'
import { fmtPct, categoryMeta } from '../utils/format.js'

export default function AlertBanner({ alert, onDismiss, onScrollToEvent }) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null

  const {
    symbol,
    kind,
    category,
    priceChgPct,
    volRatio,
    title,
    eventId,
    filingUrl,
  } = alert

  const handleDismiss = (e) => {
    e.stopPropagation()
    setDismissed(true)
    if (onDismiss) onDismiss(alert.id)
  }

  const handleClick = () => {
    if (eventId && onScrollToEvent) {
      onScrollToEvent(eventId)
    } else if (eventId) {
      const el = document.getElementById(eventId)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        el.classList.add('ring-2', 'ring-accent', 'transition-all', 'duration-500')
        setTimeout(() => {
          el.classList.remove('ring-2', 'ring-accent')
        }, 2000)
      }
    }
  }

  const isUp = (priceChgPct ?? 0) >= 0

  return (
    <div
      onClick={handleClick}
      className={clsx(
        'group relative flex items-start gap-3 p-3 rounded-xl border text-sm transition-all cursor-pointer shadow-sm',
        'hover:shadow-md hover:border-accent/40 active:scale-[0.99]',
        kind === 'combined'
          ? 'bg-gradient-to-r from-accent/15 via-warning/10 to-transparent border-accent/40'
          : kind === 'price'
            ? isUp
              ? 'bg-positive/10 border-positive/30'
              : 'bg-negative/10 border-negative/30'
            : kind === 'volume'
              ? 'bg-warning/10 border-warning/30'
              : 'bg-card border-border/80'
      )}
    >
      {/* Icon badge */}
      <div className="shrink-0 mt-0.5">
        {kind === 'combined' ? (
          <div className="w-7 h-7 rounded-lg bg-accent/20 flex items-center justify-center text-accent">
            <Sparkles size={15} />
          </div>
        ) : kind === 'price' ? (
          <div className={clsx(
            'w-7 h-7 rounded-lg flex items-center justify-center',
            isUp ? 'bg-positive/20 text-positive' : 'bg-negative/20 text-negative'
          )}>
            {isUp ? <TrendingUp size={15} /> : <TrendingDown size={15} />}
          </div>
        ) : kind === 'volume' ? (
          <div className="w-7 h-7 rounded-lg bg-warning/20 flex items-center justify-center text-warning">
            <Flame size={15} />
          </div>
        ) : (
          <div className="w-7 h-7 rounded-lg bg-card border border-border flex items-center justify-center text-accent">
            <FileText size={15} />
          </div>
        )}
      </div>

      {/* Alert Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-bold text-white text-sm">{symbol}</span>
          
          {category && (
            <span className={clsx('chip text-[9px]', categoryMeta(category).chip)}>
              {categoryMeta(category).label}
            </span>
          )}

          {priceChgPct != null && (
            <span className={clsx(
              'font-mono text-xs font-semibold px-1.5 py-0.5 rounded',
              isUp ? 'bg-positive/20 text-positive' : 'bg-negative/20 text-negative'
            )}>
              {fmtPct(priceChgPct)}
            </span>
          )}

          {volRatio != null && volRatio >= 1.5 && (
            <span className="font-mono text-xs font-semibold px-1.5 py-0.5 rounded bg-warning/20 text-warning">
              {volRatio.toFixed(1)}× vol
            </span>
          )}

          <span className="text-[10px] text-muted ml-auto mr-5 group-hover:text-accent flex items-center gap-0.5">
            View event <ArrowRight size={10} />
          </span>
        </div>

        <p className="text-xs text-white/80 mt-1 line-clamp-1 leading-snug">
          {title}
        </p>

        {/* Filing PDF Link if available */}
        {filingUrl && (
          <div className="mt-1.5 flex items-center gap-2" onClick={e => e.stopPropagation()}>
            <a
              href={filingUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[10px] text-accent hover:underline font-mono"
            >
              <ExternalLink size={10} />
              <span>Source Filing PDF</span>
            </a>
          </div>
        )}
      </div>

      {/* Dismiss Button */}
      <button
        onClick={handleDismiss}
        title="Dismiss alert"
        className="absolute top-2.5 right-2.5 p-1 rounded-full text-muted hover:text-white hover:bg-white/10 transition-colors"
      >
        <X size={13} />
      </button>
    </div>
  )
}
