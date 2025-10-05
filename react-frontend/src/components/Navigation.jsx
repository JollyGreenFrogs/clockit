function Navigation({ activeTab, onTabChange, isDesktop }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊', showOnDesktop: true, showOnMobile: true },
    { id: 'timer', label: 'Timer & Tasks', icon: '⏱️', showOnDesktop: false, showOnMobile: true }, // Combined on desktop
    { id: 'tasks', label: 'Tasks', icon: '📋', showOnDesktop: false, showOnMobile: true }, // Combined on desktop  
    { id: 'time-track', label: 'Time Tracking', icon: '⏱️', showOnDesktop: true, showOnMobile: false }, // Desktop combined view
    { id: 'rates', label: 'Rates', icon: '💰', showOnDesktop: true, showOnMobile: true },
    { id: 'currency', label: 'Currency', icon: '💱', showOnDesktop: true, showOnMobile: true },
    { id: 'invoice', label: 'Invoice', icon: '🧾', showOnDesktop: true, showOnMobile: true }
  ]

  const visibleTabs = isDesktop 
    ? tabs.filter(tab => tab.showOnDesktop)
    : tabs.filter(tab => tab.showOnMobile)

  return (
    <nav className="app-navigation">
      <div className="nav-tabs">
        {visibleTabs.map(tab => (
          <button
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="nav-icon">{tab.icon}</span>
            <span className="nav-label">{tab.label}</span>
          </button>
        ))}
      </div>
    </nav>
  )
}

export default Navigation