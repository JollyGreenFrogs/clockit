import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'

function EnhancedTaskManager({ onTasksChange, tasks: externalTasks }) {
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
    // Only load tasks locally if no external tasks provided
    if (!externalTasks || externalTasks.length === 0) {
      loadTasks()
    }
    loadCategories()
  }, [externalTasks]) // eslint-disable-line react-hooks/exhaustive-deps

  // Update local tasks when external tasks change (e.g., from timer saving time)
  useEffect(() => {
    if (externalTasks && Array.isArray(externalTasks)) {
      setTasks(externalTasks)
    }
  }, [externalTasks])

  const loadTasks = async () => {
    try {
      const response = await authenticatedFetch('/tasks')
      if (response.ok) {
        const data = await response.json()
        // Convert object format {"1": {...}, "2": {...}} to array [...] 
        const tasksData = data.tasks || {}
        const tasksArray = Object.values(tasksData)
        setTasks(tasksArray)
      }
    } catch {
      // Handle error silently
    }
  }

  const loadCategories = async () => {
    try {
      const response = await authenticatedFetch('/categories')
      if (response.ok) {
        const data = await response.json()
        // Extract category names from the categories array
        const categoriesArray = data.categories.map(cat => cat.name)
        setCategories(categoriesArray)
      }
    } catch {
      // Handle error silently
    }
  }

  // Validate task name for basic requirements only
  const validateTaskName = (name) => {
    if (!name || !name.trim()) {
      return 'Task name cannot be empty'
    }
    
    // Check for excessive spaces
    if (name.includes('  ')) {
      return 'Task name cannot contain multiple consecutive spaces.'
    }
    
    if (name !== name.trim()) {
      return 'Task name cannot start or end with spaces.'
    }
    
    if (name.length > 100) {
      return 'Task name must be 100 characters or less.'
    }
    
    return null // Valid
  }

  const createTask = async () => {
    const validationError = validateTaskName(taskName)
    if (validationError) {
      setResult(validationError)
      return
    }

    if (!selectedCategory.trim()) {
      setResult('Please select a category for the task.')
      return
    }

    setLoading(true)
    try {
      const response = await authenticatedFetch('/tasks', {
        method: 'POST',
        body: JSON.stringify({
          name: taskName.trim(),
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
        const errorData = await response.json()
        setResult(errorData.detail || 'Error creating task')
      }
    } catch {
      setResult('Error creating task')
    } finally {
      setLoading(false)
    }
  }

  const addNewCategory = async () => {
    if (!newCategoryName.trim()) return

    try {
      const response = await authenticatedFetch('/rates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_type: newCategoryName,
          day_rate: 0 // Default rate, user can set this later in rate configuration
        })
      })

      if (response.ok) {
        await loadCategories()
        setSelectedCategory(newCategoryName)
        setNewCategoryName('')
        setShowNewCategory(false)
      }
    } catch {
      // Handle error silently
    }
  }





  const deleteTask = async (taskId, taskName) => {
    try {
      setLoading(true)
      
      // Use task ID instead of encoded name
      const response = await authenticatedFetch(`/tasks/${taskId}`, {
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
      setResult(`Error deleting task: ${error.message}`)
    } finally {
      setLoading(false)
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
                <option value="">Select a category... (Required)</option>
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
        {Array.isArray(tasks) && tasks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <div className="empty-state-text">No tasks yet. Create one above!</div>
          </div>
        ) : Array.isArray(tasks) ? (
          tasks.map((task) => (
            <div key={task.id} className="task-item">
              <span className="task-name">{task.name}</span>
              <span className="task-time">{formatTime(task.time_spent)}</span>
              <button 
                onClick={() => {
                  if (window.confirm(`Are you sure you want to delete the task "${task.name}"?`)) {
                    deleteTask(task.id, task.name)
                  }
                }}
                className="btn btn-danger btn-small"
                disabled={loading}
              >
                🗑️
              </button>
            </div>
          ))
        ) : (
          // Fallback for old format
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