/** Format a UTC ISO date string to IST display */
export function toIST(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: false,
    })
  } catch { return iso }
}

/** Format a number as ₹ crores with suffix */
export function fmtCr(val) {
  if (val == null) return '—'
  const n = Number(val)
  if (isNaN(n)) return '—'
  if (Math.abs(n) >= 1_00_000) return `₹${(n / 1_00_000).toFixed(1)}L Cr`
  if (Math.abs(n) >= 1_000) return `₹${(n / 1_000).toFixed(1)}k Cr`
  return `₹${n.toFixed(0)} Cr`
}

/** Format percentage */
export function fmtPct(val) {
  if (val == null) return '—'
  const n = Number(val)
  if (isNaN(n)) return '—'
  const sign = n >= 0 ? '+' : ''
  return `${sign}${n.toFixed(2)}%`
}

/** Delta badge class */
export function deltaClass(val) {
  if (val == null) return 'text-muted'
  return Number(val) >= 0 ? 'text-positive' : 'text-negative'
}

/** How long ago (relative time) */
export function timeAgo(iso, anchorDate = null) {
  if (!iso) return ''
  const baseTime = anchorDate ? new Date(anchorDate).getTime() : Date.now()
  const targetTime = new Date(iso).getTime()
  if (isNaN(targetTime)) return ''
  const diff = Math.max(0, baseTime - targetTime)
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

/** Category → display label + chip class */
export const CATEGORY_META = {
  results:          { label: 'Results',         chip: 'chip-results',  tier: 1 },
  management_change:{ label: 'Mgmt Change',     chip: 'chip-mgmt',     tier: 1 },
  'M&A':            { label: 'M&A',             chip: 'chip-ma',       tier: 1 },
  earnings_call:    { label: 'Concall',         chip: 'chip-call',     tier: 2 },
  press_release:    { label: 'Press',           chip: 'chip-press',    tier: 2 },
  investor_meetings:{ label: 'Inv. Meet',       chip: 'chip-meetings', tier: 2 },
  unclassified:     { label: 'Routine',         chip: 'chip-other',    tier: 3 },
}

export function categoryMeta(cat) {
  return CATEGORY_META[cat] || { label: cat, chip: 'chip-other', tier: 3 }
}

/** Format score to 1 decimal */
export function fmtScore(s) {
  if (s == null) return '—'
  return Number(s).toFixed(1)
}

