import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

function PlannerIntegration() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const [configStatus, setConfigStatus] = useState(null)
  const { authenticatedFetch } = useAuth()

  const checkPlannerConfig = async () => {
    setLoading(true)
    try {
      const response = await authenticatedFetch('/planner/config')
      const data = await response.json()
      setConfigStatus(data)
      
      if (data.configured) {
        setResult('Microsoft Planner is configured and ready')
      } else {
        setResult('Microsoft Planner configuration incomplete. Missing: ' + 
          Object.entries(data.missing || {})
            .filter(([, missing]) => missing)
            .map(([key]) => key)
            .join(', '))
      }
    } catch (error) {
      console.error('Error checking config:', error)
      setResult('Error checking Planner configuration')
    } finally {
      setLoading(false)
    }
  }

  const setupPlanner = async () => {
    setResult('Please follow the setup instructions in PLANNER_SETUP.md file')
  }

  const syncPlanner = async () => {
    setLoading(true)
    try {
      const response = await authenticatedFetch('/planner/sync', {
        method: 'POST'
      })
      const data = await response.json()
      
      if (response.ok) {
        setResult(`Sync completed! ${data.tasks_synced || 0} tasks synchronized`)
      } else {
        setResult('Error syncing: ' + (data.detail || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error syncing planner:', error)
      setResult('Error syncing with Microsoft Planner')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="planner-integration">
      <div className="btn-group">
        <button 
          onClick={checkPlannerConfig} 
          disabled={loading} 
          className="btn btn-secondary"
        >
          {loading ? <span className="loading"></span> : '⚙️'} Check Config
        </button>
        <button 
          onClick={setupPlanner} 
          className="btn btn-warning"
        >
          🔧 Setup
        </button>
        <button 
          onClick={syncPlanner} 
          disabled={loading} 
          className="btn"
        >
          {loading ? <span className="loading"></span> : '🔄'} Sync Tasks
        </button>
      </div>

      {result && (
        <div className={`alert ${result.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {result}
        </div>
      )}

      {configStatus && (
        <div className="config-status" style={{ marginTop: '15px' }}>
          <h4>Configuration Status</h4>
          <div style={{ display: 'grid', gap: '8px' }}>
            <div className={`status-item ${configStatus.tenant_id_set ? 'configured' : 'missing'}`}>
              Tenant ID: {configStatus.tenant_id_set ? '✅ Set' : '❌ Missing'}
            </div>
            <div className={`status-item ${configStatus.client_id_set ? 'configured' : 'missing'}`}>
              Client ID: {configStatus.client_id_set ? '✅ Set' : '❌ Missing'}
            </div>
            <div className={`status-item ${configStatus.plan_id_set ? 'configured' : 'missing'}`}>
              Plan ID: {configStatus.plan_id_set ? '✅ Set' : '❌ Missing'}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PlannerIntegration