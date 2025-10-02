import { useState, useEffect, useCallback } from 'react'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Navigation from './components/Navigation'
import EnhancedStopwatch from './components/EnhancedStopwatch'
import EnhancedTaskManager from './components/EnhancedTaskManager'
import RateConfiguration from './components/RateConfiguration'
import CurrencySettings from './components/CurrencySettings'
import PlannerIntegration from './components/PlannerIntegration'
import InvoiceGeneration from './components/InvoiceGeneration'
import AuthPage from './components/AuthPage'
import Loading from './components/Loading'
import UserMenu from './components/UserMenu'
import './App.css'

// Main authenticated app content
function AppContent() {
  const [activeTab, setActiveTab] = useState('time-tracking')
  const [tasks, setTasks] = useState({})
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1024)
  const { isAuthenticated, loading, authenticatedFetch } = useAuth()

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const newIsDesktop = window.innerWidth >= 1024
      setIsDesktop(newIsDesktop)
      
      // Adjust active tab when switching between desktop/mobile
      if (newIsDesktop && (activeTab === 'timer' || activeTab === 'tasks')) {
        setActiveTab('time-track')
      } else if (!newIsDesktop && activeTab === 'time-track') {
        setActiveTab('timer')
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [activeTab])

  // Use useCallback to memoize loadTasks function
  const loadTasks = useCallback(async () => {
    try {
      const response = await authenticatedFetch('/tasks')
      if (response.ok) {
        const data = await response.json()
        setTasks(data.tasks || {})
      } else {
        console.error('Failed to load tasks:', response.status)
      }
    } catch (error) {
      console.error('Error loading tasks:', error)
    }
  }, [authenticatedFetch])

  // Load tasks for timer component (authenticated)
  useEffect(() => {
    if (isAuthenticated) {
      loadTasks()
    }
  }, [isAuthenticated, loadTasks])

  const handleSaveToTask = async (taskName, timeToSave) => {
    try {
      const response = await authenticatedFetch('/tasks', {
        method: 'POST',
        body: JSON.stringify({
          name: taskName,
          description: `Time entry from timer: ${timeToSave}ms`,
        })
      })

      // Also add time entry
      if (response.ok) {
        const timeResponse = await authenticatedFetch(`/tasks/${taskName}/time`, {
          method: 'POST',
          body: JSON.stringify({
            task_id: taskName,
            hours: timeToSave / (1000 * 60 * 60), // Convert ms to hours
            date: new Date().toISOString().split('T')[0],
            description: `Timer session: ${(timeToSave / (1000 * 60)).toFixed(1)} minutes`
          })
        })
        
        if (timeResponse.ok) {
          await loadTasks()
        }
      }
    } catch (error) {
      console.error('Error saving time to task:', error)
    }
  }

  // Show loading while checking authentication
  if (loading) {
    return <Loading />
  }

  // Show auth page if not authenticated
  if (!isAuthenticated) {
    return <AuthPage />
  }

  const renderActiveSection = () => {
    switch (activeTab) {
      case 'time-track':
        // Desktop: Combined Timer + Tasks view
        return (
          <div className="combined-section">
            <div className="timer-tasks-layout">
              <div className="timer-column">
                <div className="section">
                  <h3>
                    <span className="section-icon">⏱️</span>
                    Time Tracking
                  </h3>
                  <EnhancedStopwatch 
                    tasks={tasks}
                    onSaveToTask={handleSaveToTask}
                  />
                </div>
              </div>
              
              <div className="tasks-column">
                <div className="section">
                  <h3>
                    <span className="section-icon">📋</span>
                    Task Management
                  </h3>
                  <EnhancedTaskManager 
                    onTasksChange={loadTasks}
                  />
                </div>
              </div>
            </div>
          </div>
        )

      case 'timer':
        // Mobile: Timer only
        return (
          <div className="section">
            <h3>
              <span className="section-icon">⏱️</span>
              Time Tracking
            </h3>
            <EnhancedStopwatch 
              tasks={tasks}
              onSaveToTask={handleSaveToTask}
            />
          </div>
        )
      
      case 'tasks':
        // Mobile: Tasks only
        return (
          <div className="section">
            <h3>
              <span className="section-icon">📋</span>
              Task Management
            </h3>
            <EnhancedTaskManager 
              onTasksChange={loadTasks}
            />
          </div>
        )
      
      case 'rates':
        return (
          <div className="section">
            <h3>
              <span className="section-icon">💰</span>
              Rate Configuration
            </h3>
            <RateConfiguration />
          </div>
        )
      
      case 'currency':
        return (
          <div className="section">
            <h3>
              <span className="section-icon">💱</span>
              Currency Settings
            </h3>
            <CurrencySettings />
          </div>
        )
      
      case 'planner':
        return (
          <div className="section">
            <h3>
              <span className="section-icon">🔗</span>
              Microsoft Planner
            </h3>
            <PlannerIntegration />
          </div>
        )
      
      case 'invoice':
        return (
          <div className="section invoice-section">
            <h3>
              <span className="section-icon">🧾</span>
              Invoice Generation
            </h3>
            <InvoiceGeneration />
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <div className="app">
      <div className="header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="app-title">⏰ ClockIt</h1>
            <span className="tagline">Professional Time Tracking</span>
          </div>
          <div className="header-right">
            <UserMenu />
          </div>
        </div>
      </div>
      
      <Navigation 
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isDesktop={isDesktop}
      />
      
      <main className="main-content">
        {renderActiveSection()}
      </main>
    </div>
  )
}

// Main App component with AuthProvider
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App