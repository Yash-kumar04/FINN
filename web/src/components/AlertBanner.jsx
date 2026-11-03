import { TrendingUp, TrendingDown, Flame, X } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { fmtPct } from '../utils/format.js'

export default function AlertBanner({ symbol, alertData, type, threshold }) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null

  const isPrice = type === 'price'
  const isUp = alertData.priceChgPct >= 0

  return (
    <div className={clsx(
      'flex items-center gap-2 px-3 py-2 rounded-lg text-sm border',
      isPrice
        ? isUp
          ? 'bg-positive/10 border-positive/30 text-positive'
          : 'bg-negative/10 border-negative/30 text-negative'
        : 'bg-warning/10 border-warning/30 text-warning'
    )}>
      {isPrice
        ? isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />
        : <Flame size={14} />
      }
      <span className="font-semibold">{symbol.replace(/\.NS$/, '')}</span>
      {isPrice ? (
        <span className="font-mono">{fmtPct(alertData.priceChgPct)}</span>
      ) : (
        <span className="font-mono">{alertData.volRatio?.toFixed(1)}× avg vol</span>
      )}
      <span className="text-xs opacity-70 ml-1">
        {isPrice ? `≥ ${threshold}% threshold` : `≥ ${threshold}× threshold`}
      </span>
      <button onClick={() => setDismissed(true)} className="ml-auto opacity-50 hover:opacity-100">
        <X size={12} />
      </button>
    </div>
  )
}

