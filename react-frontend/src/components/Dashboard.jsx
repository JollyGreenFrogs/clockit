import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import TaskAuditModal from './TaskAuditModal'
import './Dashboard.css'

function Dashboard() {
  const [dashboardData, setDashboardData] = useState({
    tasks: [],
    rates: {},
    currency: null,
    loading: true
  })
  const [selectedTask, setSelectedTask] = useState(null)
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false)
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

      // Process tasks data - convert object to array
      let tasks = []
      if (tasksResponse.ok) {
        const tasksData = await tasksResponse.json()
        if (tasksData.tasks) {
          // Convert object format {"1": {...}, "2": {...}} to array [...] 
          tasks = Object.values(tasksData.tasks)
        }
      }

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
    
    // Tasks are now always an array
    const totalTasks = tasks.length
    const totalHours = tasks.reduce((sum, task) => sum + (task.time_spent || 0), 0)
    
    // Calculate estimated income
    let totalIncome = 0
    tasks.forEach(task => {
      // Try to find a matching rate for this task
      const taskRate = Object.entries(rates).find(([rateType]) => 
        task.name.toLowerCase().includes(rateType.toLowerCase()) || 
        rateType.toLowerCase().includes(task.name.toLowerCase())
      )
      
      if (taskRate) {
        const hourlyRate = taskRate[1] / 8 // Convert day rate to hourly
        totalIncome += (task.time_spent || 0) * hourlyRate
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
    // Handle invalid input
    if (typeof hours !== 'number' || isNaN(hours) || hours < 0) {
      return '00:00:00'
    }
    
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
    
    // Tasks are now always an array
    return tasks
      .filter(task => task.time_spent > 0) // Only show tasks with actual time
      .sort((a, b) => b.time_spent - a.time_spent) // Sort by time spent (descending)
      .slice(0, 5) // Top 5 tasks
  }

  const openTaskAudit = (task) => {
    setSelectedTask(task)
    setIsAuditModalOpen(true)
  }

  const closeTaskAudit = () => {
    setIsAuditModalOpen(false)
    setSelectedTask(null)
  }

  const handleTaskUpdate = (updatedTask) => {
    // Update the task in the dashboard data
    setDashboardData(prev => ({
      ...prev,
      tasks: prev.tasks.map(task => 
        task.id === updatedTask.id ? updatedTask : task
      )
    }))
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
      <section className="stats-grid" aria-label="Dashboard Statistics">
        <div className="stat-card" role="region" aria-labelledby="total-tasks-label">
          <div className="stat-icon" aria-hidden="true">📋</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totalTasks}</div>
            <div className="stat-label" id="total-tasks-label">Total Tasks</div>
          </div>
        </div>

        <div className="stat-card" role="region" aria-labelledby="total-time-label">
          <div className="stat-icon" aria-hidden="true">⏰</div>
          <div className="stat-content">
            <div className="stat-value">{formatTime(stats.totalHours)}</div>
            <div className="stat-label" id="total-time-label">Total Time</div>
          </div>
        </div>

        <div className="stat-card" role="region" aria-labelledby="estimated-income-label">
          <div className="stat-icon" aria-hidden="true">💰</div>
          <div className="stat-content">
            <div className="stat-value">{formatCurrency(stats.totalIncome)}</div>
            <div className="stat-label" id="estimated-income-label">Estimated Income</div>
          </div>
        </div>

        <div className="stat-card" role="region" aria-labelledby="avg-per-task-label">
          <div className="stat-icon" aria-hidden="true">📈</div>
          <div className="stat-content">
            <div className="stat-value">{formatTime(stats.averageHoursPerTask)}</div>
            <div className="stat-label" id="avg-per-task-label">Avg. per Task</div>
          </div>
        </div>
      </section>

      {/* Recent Tasks */}
      <div className="dashboard-section">
        <h3>
          <span className="section-icon">🔥</span>
          Top Tasks by Time
        </h3>
        {recentTasks.length > 0 ? (
          <div className="recent-tasks">
            {recentTasks.map((task) => (
              <div 
                key={task.id} 
                className="task-summary clickable"
                onClick={() => openTaskAudit(task)}
                title="Click to view task audit trail"
              >
                <div className="task-summary-main">
                  <div className="task-summary-name">{task.name}</div>
                  {task.category && (
                    <div className="task-summary-category">📁 {task.category}</div>
                  )}
                  {task.description && (
                    <div className="task-summary-description">{task.description}</div>
                  )}
                </div>
                <div className="task-summary-time">{formatTime(task.time_spent)}</div>
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

      {/* Task Audit Modal */}
      <TaskAuditModal
        task={selectedTask}
        isOpen={isAuditModalOpen}
        onClose={closeTaskAudit}
        onTaskUpdate={handleTaskUpdate}
      />
    </div>
  )
}

export default Dashboard