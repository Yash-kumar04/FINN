import { useState } from 'react'
import { Bell, Search } from 'lucide-react'
import BriefingTab from './tabs/BriefingTab.jsx'
import ResearchTab from './tabs/ResearchTab.jsx'
import { useSnapshot } from './hooks/useSnapshot.js'
import clsx from 'clsx'

export default function App() {
  const [activeTab, setActiveTab] = useState('briefing')
  const [todayAlertsCount, setTodayAlertsCount] = useState(0)
  const { data: prices } = useSnapshot('prices.json')
  const asOfDate = prices?.provenance?.as_of_date || '2026-11-02'

  return (
    <div className="flex flex-col h-full max-w-lg mx-auto bg-surface relative">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-border bg-card sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg tracking-tight text-white">FINN</span>
          <span className="text-muted text-xs font-mono">/ financial intelligence</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="chip chip-other text-[10px] font-mono">Data as of {asOfDate}</span>
          {todayAlertsCount > 0 && (
            <button
              onClick={() => {
                setActiveTab('briefing')
                window.scrollTo({ top: 0, behavior: 'smooth' })
              }}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-accent/20 border border-accent/40 text-accent text-[11px] font-semibold hover:bg-accent/30 transition-colors shadow-sm"
              title="View today's fired alerts"
            >
              <Bell size={11} className="animate-pulse" />
              <span>Today's alerts: {todayAlertsCount}</span>
            </button>
          )}
        </div>
      </header>

      {/* Tab content */}
      <main className="flex-1 overflow-y-auto pb-20">
        {activeTab === 'briefing' && <BriefingTab onAlertsCountChange={setTodayAlertsCount} />}
        {activeTab === 'research' && <ResearchTab />}
      </main>

      {/* Bottom tab bar */}
      <nav className="tab-bar">
        <button
          className={clsx('tab-btn', activeTab === 'briefing' && 'active')}
          onClick={() => setActiveTab('briefing')}
        >
          <Bell size={20} strokeWidth={activeTab === 'briefing' ? 2.5 : 1.5} />
          <span className="tab-label">Briefing</span>
        </button>
        <button
          className={clsx('tab-btn', activeTab === 'research' && 'active')}
          onClick={() => setActiveTab('research')}
        >
          <Search size={20} strokeWidth={activeTab === 'research' ? 2.5 : 1.5} />
          <span className="tab-label">Research</span>
        </button>
      </nav>
    </div>
  )
}

