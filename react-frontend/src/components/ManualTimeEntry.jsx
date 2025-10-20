import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

function ManualTimeEntry({ tasks, onTimeAdded }) {
  const [selectedTask, setSelectedTask] = useState('')
  const [timeHours, setTimeHours] = useState('')
  const [timeDate, setTimeDate] = useState(new Date().toISOString().split('T')[0])
  const [timeDescription, setTimeDescription] = useState('')
  const [result, setResult] = useState('')
  const { authenticatedFetch } = useAuth()

  const addTimeEntry = async () => {
    if (!selectedTask || !timeHours) {
      setResult('Please select a task and enter hours')
      return
    }

    try {
      // selectedTask is now the task ID
      const response = await authenticatedFetch(`/tasks/${selectedTask}/time`, {
        method: 'POST',
        body: JSON.stringify({
          task_id: selectedTask,
          hours: parseFloat(timeHours),
          date: timeDate,
          description: timeDescription
        })
      })

      if (response.ok) {
        if (onTimeAdded) onTimeAdded()
        setTimeHours('')
        setTimeDescription('')
        setResult('Time entry added successfully!')
        // Clear result after 3 seconds
        setTimeout(() => setResult(''), 3000)
      } else {
        const errorData = await response.json()
        setResult(errorData.detail || 'Error adding time entry')
        setTimeout(() => setResult(''), 5000)
      }
    } catch (error) {
      console.error('Error adding time entry:', error)
      setResult('Error adding time entry')
      setTimeout(() => setResult(''), 3000)
    }
  }

  return (
    <div className="time-entry-section">
      <h4>Manual Time Entry</h4>
      <div className="form-grid">
        <div className="form-row">
          <label>Select Task:</label>
          <select 
            value={selectedTask}
            onChange={(e) => setSelectedTask(e.target.value)}
          >
            <option value="">Select a task...</option>
            {Array.isArray(tasks) ? tasks.map(task => (
              <option key={task.id} value={task.id}>{task.name}</option>
            )) : Object.keys(tasks).map(taskName => (
              <option key={taskName} value={taskName}>{taskName}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label>Hours:</label>
          <input
            type="number"
            value={timeHours}
            onChange={(e) => setTimeHours(e.target.value)}
            step="0.25"
            min="0"
            placeholder="e.g., 2.5"
          />
        </div>
        <div className="form-row">
          <label>Date:</label>
          <input
            type="date"
            value={timeDate}
            onChange={(e) => setTimeDate(e.target.value)}
          />
        </div>
        <div className="form-row">
          <label>Description:</label>
          <input
            type="text"
            value={timeDescription}
            onChange={(e) => setTimeDescription(e.target.value)}
            placeholder="What you worked on"
          />
        </div>
      </div>

      <button onClick={addTimeEntry} className="btn btn-success">
        ⏰ Add Time Entry
      </button>

      {/* Results */}
      {result && (
        <div className={`alert ${result.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {result}
        </div>
      )}
    </div>
  )
}

export default ManualTimeEntry