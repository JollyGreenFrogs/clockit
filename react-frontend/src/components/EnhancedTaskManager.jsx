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
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const { authenticatedFetch } = useAuth()

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





  const deleteTask = async (taskName) => {
    try {
      setLoading(true)
      console.log('Deleting task:', taskName)
      
      // URL encode the task name to handle special characters
      const encodedTaskName = encodeURIComponent(taskName)
      const response = await authenticatedFetch(`/tasks/${encodedTaskName}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setResult(`Task "${taskName}" deleted successfully`)
        await loadTasks()
        if (onTasksChange) onTasksChange()
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Failed to delete task: ${response.status}`)
      }
    } catch (error) {
      console.error('Error deleting task:', error)
      setResult(`Error deleting task: ${error.message}`)
    } finally {
      setLoading(false)
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
                onClick={() => {
                  if (window.confirm(`Are you sure you want to delete the task "${taskName}"?`)) {
                    deleteTask(taskName)
                  }
                }}
                className="btn btn-danger btn-small"
                disabled={loading}
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