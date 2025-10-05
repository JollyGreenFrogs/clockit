import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './Dashboard.css'

function Dashboard() {
  const [dashboardData, setDashboardData] = useState({
    tasks: {},
    rates: {},
    currency: null,
    loading: true
  })
  const { authenticatedFetch } = useAuth()

  const loadDashboardData = useCallback(async () => {
    try {
      setDashboardData(prev => ({ ...prev, loading: true }))
      
      // Load all data in parallel
      const [tasksResponse, ratesResponse, currencyResponse] = await Promise.all([
        authenticatedFetch('/tasks'),
        authenticatedFetch('/rates'),
        authenticatedFetch('/currency').catch(() => ({ ok: false })) // Currency might not be set
      ])

      const tasks = tasksResponse.ok ? (await tasksResponse.json()).tasks || {} : {}
      const rates = ratesResponse.ok ? (await ratesResponse.json()) : {}
      const currency = currencyResponse.ok ? (await currencyResponse.json()).currency : null

      setDashboardData({
        tasks,
        rates,
        currency,
        loading: false
      })
    } catch (error) {
      console.error('Error loading dashboard data:', error)
      setDashboardData(prev => ({ ...prev, loading: false }))
    }
  }, [authenticatedFetch])

  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  const calculateStats = () => {
    const { tasks, rates } = dashboardData
    
    const totalTasks = Object.keys(tasks).length
    const totalHours = Object.values(tasks).reduce((sum, hours) => sum + hours, 0)
    
    // Calculate estimated income
    let totalIncome = 0
    Object.entries(tasks).forEach(([taskName, hours]) => {
      // Try to find a matching rate for this task
      const taskRate = Object.entries(rates).find(([rateType]) => 
        taskName.toLowerCase().includes(rateType.toLowerCase()) || 
        rateType.toLowerCase().includes(taskName.toLowerCase())
      )
      
      if (taskRate) {
        const hourlyRate = taskRate[1] / 8 // Convert day rate to hourly
        totalIncome += hours * hourlyRate
      }
    })

    return {
      totalTasks,
      totalHours,
      totalIncome,
      averageHoursPerTask: totalTasks > 0 ? totalHours / totalTasks : 0
    }
  }

  const formatTime = (hours) => {
    const totalHours = Math.floor(hours)
    const minutes = Math.floor((hours % 1) * 60)
    const seconds = Math.floor(((hours % 1) * 60 % 1) * 60)

    return `${totalHours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }

  const formatCurrency = (amount) => {
    const { currency } = dashboardData
    if (!currency) return `$${amount.toFixed(2)}`
    
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency.code || 'USD'
      }).format(amount)
    } catch {
      return `${currency.symbol || '$'}${amount.toFixed(2)}`
    }
  }

  const getRecentTasks = () => {
    const { tasks } = dashboardData
    return Object.entries(tasks)
      .sort(([,a], [,b]) => b - a) // Sort by time spent (descending)
      .slice(0, 5) // Top 5 tasks
  }

  if (dashboardData.loading) {
    return (
      <div className="dashboard">
        <div className="dashboard-loading">
          <div className="loading-spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const stats = calculateStats()
  const recentTasks = getRecentTasks()

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>
          <span className="dashboard-icon">📊</span>
          Dashboard
        </h2>
        <p className="dashboard-subtitle">Overview of your time tracking and productivity</p>
      </div>

      {/* Quick Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totalTasks}</div>
            <div className="stat-label">Total Tasks</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏰</div>
          <div className="stat-content">
            <div className="stat-value">{formatTime(stats.totalHours)}</div>
            <div className="stat-label">Total Time</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <div className="stat-value">{formatCurrency(stats.totalIncome)}</div>
            <div className="stat-label">Estimated Income</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-value">{formatTime(stats.averageHoursPerTask)}</div>
            <div className="stat-label">Avg. per Task</div>
          </div>
        </div>
      </div>

      {/* Recent Tasks */}
      <div className="dashboard-section">
        <h3>
          <span className="section-icon">🔥</span>
          Top Tasks by Time
        </h3>
        {recentTasks.length > 0 ? (
          <div className="recent-tasks">
            {recentTasks.map(([taskName, timeSpent]) => (
              <div key={taskName} className="task-summary">
                <div className="task-summary-name">{taskName}</div>
                <div className="task-summary-time">{formatTime(timeSpent)}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <div className="empty-state-text">No tasks yet. Start tracking your time!</div>
          </div>
        )}
      </div>

      {/* Rate Configuration Status */}
      <div className="dashboard-section">
        <h3>
          <span className="section-icon">⚙️</span>
          Configuration Status
        </h3>
        <div className="config-status">
          <div className="config-item">
            <span className="config-label">Currency:</span>
            <span className={`config-value ${dashboardData.currency ? 'configured' : 'not-configured'}`}>
              {dashboardData.currency ? 
                `${dashboardData.currency.name} (${dashboardData.currency.code})` : 
                'Not set'
              }
            </span>
          </div>
          <div className="config-item">
            <span className="config-label">Rate Types:</span>
            <span className={`config-value ${Object.keys(dashboardData.rates).length > 0 ? 'configured' : 'not-configured'}`}>
              {Object.keys(dashboardData.rates).length > 0 ? 
                `${Object.keys(dashboardData.rates).length} configured` : 
                'None configured'
              }
            </span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <h3>
          <span className="section-icon">🚀</span>
          Quick Actions
        </h3>
        <div className="quick-actions">
          <div className="action-card">
            <div className="action-icon">⏱️</div>
            <div className="action-content">
              <div className="action-title">Start Tracking</div>
              <div className="action-desc">Begin timing your work</div>
            </div>
          </div>
          <div className="action-card">
            <div className="action-icon">📋</div>
            <div className="action-content">
              <div className="action-title">Manage Tasks</div>
              <div className="action-desc">Create and organize tasks</div>
            </div>
          </div>
          <div className="action-card">
            <div className="action-icon">💰</div>
            <div className="action-content">
              <div className="action-title">Set Rates</div>
              <div className="action-desc">Configure billing rates</div>
            </div>
          </div>
          <div className="action-card">
            <div className="action-icon">🧾</div>
            <div className="action-content">
              <div className="action-title">Generate Invoice</div>
              <div className="action-desc">Create billing documents</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard