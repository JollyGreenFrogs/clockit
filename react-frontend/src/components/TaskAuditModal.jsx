import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../hooks/useAuth'
import './TaskAuditModal.css'

function TaskAuditModal({ task, isOpen, onClose, onTaskUpdate }) {
  const [timeEntries, setTimeEntries] = useState([])
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(task?.category || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [editingEntry, setEditingEntry] = useState(null)
  const { authenticatedFetch } = useAuth()

  const loadTimeEntries = useCallback(async () => {
    if (!task) return
    try {
      setLoading(true)
      const response = await authenticatedFetch(`/tasks/${task.id}/time-entries`)
      if (response.ok) {
        const data = await response.json()
        setTimeEntries(data.time_entries || [])
      } else {
        setError('Failed to load time entries')
      }
    } catch {
      setError('Failed to load time entries')
    } finally {
      setLoading(false)
    }
  }, [task, authenticatedFetch])

  const loadCategories = useCallback(async () => {
    try {
      const response = await authenticatedFetch('/categories')
      if (response.ok) {
        const data = await response.json()
        // Use the categories array directly from the API response
        setCategories(data.categories || [])
      }
    } catch {
      // Handle error silently
    }
  }, [authenticatedFetch])

  useEffect(() => {
    if (isOpen && task) {
      loadTimeEntries()
      loadCategories()
      setSelectedCategory(task.category || '')
    }
  }, [isOpen, task, loadTimeEntries, loadCategories])

  const updateTaskCategory = async () => {
    try {
      setLoading(true)
      const response = await authenticatedFetch(`/tasks/${task.id}/category`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: selectedCategory })
      })
      
      if (response.ok) {
        // Update the task object and notify parent
        const updatedTask = { ...task, category: selectedCategory }
        onTaskUpdate && onTaskUpdate(updatedTask)
        setError('')
      } else {
        setError('Failed to update task category')
      }
    } catch {
      setError('Failed to update task category')
    } finally {
      setLoading(false)
    }
  }

  const deleteTimeEntry = async (entryId) => {
    if (!window.confirm('Are you sure you want to delete this time entry?')) {
      return
    }

    try {
      setLoading(true)
      const response = await authenticatedFetch(`/time-entries/${entryId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setTimeEntries(timeEntries.filter(entry => entry.id !== entryId))
        setError('')
      } else {
        setError('Failed to delete time entry')
      }
    } catch {
      setError('Failed to delete time entry')
    } finally {
      setLoading(false)
    }
  }

  const updateTimeEntry = async (entryId, duration, description) => {
    try {
      setLoading(true)
      const response = await authenticatedFetch(`/time-entries/${entryId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration, description })
      })
      
      if (response.ok) {
        // Reload time entries to get updated data
        await loadTimeEntries()
        setEditingEntry(null)
        setError('')
      } else {
        setError('Failed to update time entry')
      }
    } catch {
      setError('Failed to update time entry')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (hours) => {
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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  const getTotalTime = () => {
    return timeEntries.reduce((total, entry) => total + (entry.duration || 0), 0)
  }

  if (!isOpen || !task) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="task-audit-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📋 Task Audit Trail</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="modal-content">
          {/* Task Information */}
          <div className="task-info">
            <h3>{task.name}</h3>
            {task.description && <p className="task-description">{task.description}</p>}
            
            {/* Category Editor */}
            <div className="category-editor">
              <label htmlFor="task-category">Category:</label>
              <div className="category-input-group">
                <select
                  id="task-category"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  disabled={loading}
                >
                  <option value="">Select a category</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.name}>
                      {category.name}
                    </option>
                  ))}
                </select>
                <button 
                  onClick={updateTaskCategory}
                  disabled={loading || selectedCategory === task.category}
                  className="btn btn-primary btn-small"
                >
                  Update
                </button>
              </div>
            </div>

            <div className="task-stats">
              <span className="stat">Total Time: {formatTime(getTotalTime())}</span>
              <span className="stat">Time Entries: {timeEntries.length}</span>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          {/* Time Entries */}
          <div className="time-entries">
            <h4>Time Entry History</h4>
            
            {loading && (
              <div className="loading">Loading time entries...</div>
            )}

            {!loading && timeEntries.length === 0 && (
              <div className="empty-state">
                <div className="empty-state-icon">⏰</div>
                <div className="empty-state-text">No time entries recorded yet</div>
              </div>
            )}

            {!loading && timeEntries.length > 0 && (
              <div className="entries-list">
                {timeEntries.map(entry => (
                  <div key={entry.id} className="time-entry">
                    {editingEntry === entry.id ? (
                      <TimeEntryEditor
                        entry={entry}
                        onSave={(duration, description) => updateTimeEntry(entry.id, duration, description)}
                        onCancel={() => setEditingEntry(null)}
                        formatTime={formatTime}
                      />
                    ) : (
                      <TimeEntryDisplay
                        entry={entry}
                        onEdit={() => setEditingEntry(entry.id)}
                        onDelete={() => deleteTimeEntry(entry.id)}
                        formatTime={formatTime}
                        formatDate={formatDate}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

function TimeEntryDisplay({ entry, onEdit, onDelete, formatTime, formatDate }) {
  return (
    <>
      <div className="entry-main">
        <div className="entry-time">{formatTime(entry.duration)}</div>
        <div className="entry-details">
          <div className="entry-date">{formatDate(entry.created_at)}</div>
          {entry.description && (
            <div className="entry-description">{entry.description}</div>
          )}
        </div>
      </div>
      <div className="entry-actions">
        <button
          className="btn btn-small btn-secondary"
          onClick={onEdit}
          title="Edit time entry"
        >
          ✏️
        </button>
        <button
          className="btn btn-small btn-danger"
          onClick={onDelete}
          title="Delete time entry"
        >
          🗑️
        </button>
      </div>
    </>
  )
}

function TimeEntryEditor({ entry, onSave, onCancel, formatTime }) {
  const [duration, setDuration] = useState(entry.duration || 0)
  const [description, setDescription] = useState(entry.description || '')

  const handleSave = () => {
    onSave(duration, description)
  }

  return (
    <>
      <div className="entry-main">
        <div className="entry-editor">
          <div className="editor-field">
            <label>Duration (hours):</label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={duration}
              onChange={(e) => setDuration(parseFloat(e.target.value) || 0)}
            />
            <span className="time-preview">{formatTime(duration)}</span>
          </div>
          <div className="editor-field">
            <label>Description:</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description..."
              rows={2}
            />
          </div>
        </div>
      </div>
      <div className="entry-actions">
        <button
          className="btn btn-small btn-primary"
          onClick={handleSave}
        >
          💾 Save
        </button>
        <button
          className="btn btn-small btn-secondary"
          onClick={onCancel}
        >
          ✕ Cancel
        </button>
      </div>
    </>
  )
}

export default TaskAuditModal