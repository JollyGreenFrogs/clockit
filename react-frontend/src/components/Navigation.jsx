function Navigation({ activeTab, onTabChange, isDesktop }) {
  const tabs = [
    { id: 'timer', label: 'Timer & Tasks', icon: '⏱️', showOnDesktop: false }, // Combined on desktop
    { id: 'tasks', label: 'Tasks', icon: '📋', showOnDesktop: false }, // Combined on desktop  
    { id: 'time-track', label: 'Time Tracking', icon: '⏱️', showOnDesktop: true }, // Desktop combined view
    { id: 'rates', label: 'Rates', icon: '💰', showOnDesktop: true },
    { id: 'currency', label: 'Currency', icon: '💱', showOnDesktop: true },
    { id: 'planner', label: 'Planner', icon: '🔗', showOnDesktop: true },
    { id: 'invoice', label: 'Invoice', icon: '🧾', showOnDesktop: true }
  ]

  const visibleTabs = isDesktop 
    ? tabs.filter(tab => tab.showOnDesktop)
    : tabs.filter(tab => !tab.showOnDesktop)

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