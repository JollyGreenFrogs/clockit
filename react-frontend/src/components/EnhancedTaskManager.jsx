import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

function EnhancedTaskManager({ onTasksChange }) {
  const [tasks, setTasks] = useState({})
  const [categories, setCategories] = useState([])
  const [taskName, setTaskName] = useState('')
  const [taskDescription, setTaskDescription] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [newCategoryName, setNewCategoryName] = useState('')
  const [showNewCategory, setShowNewCategory] = useState(false)
  const [selectedTask, setSelectedTask] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const { authenticatedFetch } = useAuth()

  // Time entry fields
  const [timeHours, setTimeHours] = useState('')
  const [timeDate, setTimeDate] = useState(new Date().toISOString().split('T')[0])
  const [timeDescription, setTimeDescription] = useState('')

  useEffect(() => {
    loadTasks()
    loadCategories()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loadTasks = async () => {
    try {
      const response = await authenticatedFetch('/tasks')
      if (response.ok) {
        const data = await response.json()
        setTasks(data.tasks || {})
      }
    } catch (error) {
      console.error('Error loading tasks:', error)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await authenticatedFetch('/categories')
      if (response.ok) {
        const data = await response.json()
        setCategories(data.categories || [])
      }
    } catch (error) {
      console.error('Error loading categories:', error)
    }
  }

  const createTask = async () => {
    if (!taskName.trim()) {
      setResult('Please enter a task name')
      return
    }

    setLoading(true)
    try {
      const response = await authenticatedFetch('/tasks', {
        method: 'POST',
        body: JSON.stringify({
          name: taskName,
          description: taskDescription,
          category: selectedCategory
        })
      })

      if (response.ok) {
        setResult('Task created successfully!')
        setTaskName('')
        setTaskDescription('')
        setSelectedCategory('')
        await loadTasks()
        if (onTasksChange) onTasksChange()
      } else {
        setResult('Error creating task')
      }
    } catch (error) {
      console.error('Error creating task:', error)
      setResult('Error creating task')
    } finally {
      setLoading(false)
    }
  }

  const addNewCategory = async () => {
    if (!newCategoryName.trim()) return

    try {
      const response = await authenticatedFetch('/categories', {
        method: 'POST',
        body: JSON.stringify({
          name: newCategoryName,
          description: ''
        })
      })

      if (response.ok) {
        await loadCategories()
        setSelectedCategory(newCategoryName)
        setNewCategoryName('')
        setShowNewCategory(false)
      }
    } catch (error) {
      console.error('Error adding category:', error)
    }
  }



  const addTimeEntry = async () => {
    if (!selectedTask || !timeHours) {
      setResult('Please select a task and enter hours')
      return
    }

    try {
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
        await loadTasks()
        if (onTasksChange) onTasksChange()
        setTimeHours('')
        setTimeDescription('')
        setResult('Time entry added successfully!')
      }
    } catch (error) {
      console.error('Error adding time entry:', error)
      setResult('Error adding time entry')
    }
  }

  const deleteTask = async (taskName) => {
    try {
      await authenticatedFetch(`/tasks/${taskName}`, {
        method: 'DELETE'
      })
      await loadTasks()
      if (onTasksChange) onTasksChange()
    } catch (error) {
      console.error('Error deleting task:', error)
    }
  }

  const formatTime = (milliseconds) => {
    const hours = Math.floor(milliseconds / 3600000)
    const minutes = Math.floor((milliseconds % 3600000) / 60000)
    const seconds = Math.floor((milliseconds % 60000) / 1000)

    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }

  return (
    <div className="enhanced-task-manager">
      {/* Task Creation */}
      <div className="task-creation-section">
        <h4>Create New Task</h4>
        <div className="form-grid">
          <div className="form-row">
            <label>Task Name:</label>
            <input
              type="text"
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              placeholder="Enter task name"
            />
          </div>
          <div className="form-row">
            <label>Description:</label>
            <textarea
              value={taskDescription}
              onChange={(e) => setTaskDescription(e.target.value)}
              placeholder="Task description (optional)"
            />
          </div>
          <div className="form-row">
            <label>Category:</label>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <select 
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                style={{ flex: 1 }}
              >
                <option value="">Select a category...</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => setShowNewCategory(true)}
              >
                ➕ New
              </button>
            </div>
            {showNewCategory && (
              <div style={{ marginTop: '10px' }}>
                <input
                  type="text"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  placeholder="Enter new category name"
                  style={{ width: '100%', marginBottom: '10px' }}
                />
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button onClick={addNewCategory} className="btn" style={{ flex: 1 }}>
                    ✅ Add Category
                  </button>
                  <button 
                    onClick={() => {
                      setShowNewCategory(false)
                      setNewCategoryName('')
                    }} 
                    className="btn btn-secondary" 
                    style={{ flex: 1 }}
                  >
                    ❌ Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="btn-group">
          <button onClick={createTask} disabled={loading} className="btn">
            {loading ? <span className="loading"></span> : '➕'} Create Task
          </button>
          <button onClick={loadTasks} className="btn btn-secondary">
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Manual Time Entry */}
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
              {Object.keys(tasks).map(taskName => (
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
      </div>

      {/* Results */}
      {result && (
        <div className={`alert ${result.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {result}
        </div>
      )}

      {/* Tasks List */}
      <div className="task-list">
        <h4>Current Tasks</h4>
        {Object.keys(tasks).length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <div className="empty-state-text">No tasks yet. Create one above!</div>
          </div>
        ) : (
          Object.entries(tasks).map(([taskName, timeSpent]) => (
            <div key={taskName} className="task-item">
              <span className="task-name">{taskName}</span>
              <span className="task-time">{formatTime(timeSpent)}</span>
              <button 
                onClick={() => deleteTask(taskName)}
                className="btn btn-danger btn-small"
              >
                🗑️
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default EnhancedTaskManager