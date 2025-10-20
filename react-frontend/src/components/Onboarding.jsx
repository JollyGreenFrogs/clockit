import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './Onboarding.css'

function Onboarding() {
  const [defaultCategory, setDefaultCategory] = useState('')
  const [initialCategories, setInitialCategories] = useState([''])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const { authenticatedFetch, user, refreshUser } = useAuth()

  const addCategoryField = () => {
    setInitialCategories([...initialCategories, ''])
  }

  const removeCategoryField = (index) => {
    setInitialCategories(initialCategories.filter((_, i) => i !== index))
  }

  const updateCategoryField = (index, value) => {
    const updated = [...initialCategories]
    updated[index] = value
    setInitialCategories(updated)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!defaultCategory.trim()) {
      setError('Default category is required')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await authenticatedFetch('/onboarding/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          default_category: defaultCategory.trim(),
          initial_categories: initialCategories.filter(cat => cat.trim())
        })
      })

      if (response.ok) {
        await refreshUser() // Refresh user data to update onboarding status
        // The AuthContext will handle redirecting to dashboard
      } else {
        const data = await response.json()
        setError(data.detail || 'Failed to complete onboarding')
      }
    } catch (error) {
      console.error('Onboarding error:', error)
      setError('Network error during onboarding')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="onboarding-container">
      <div className="onboarding-card">
        <div className="onboarding-header">
          <h1>Welcome to ClockIt! 🚀</h1>
          <p>Hi {user?.full_name || user?.username}! Let's set up your workspace for time tracking and invoicing.</p>
        </div>

        <form onSubmit={handleSubmit} className="onboarding-form">
          <div className="form-section">
            <h3>Default Task Category</h3>
            <p>This will be your primary category for new tasks and invoicing:</p>
            <input
              type="text"
              value={defaultCategory}
              onChange={(e) => setDefaultCategory(e.target.value)}
              placeholder="e.g., Development, Consulting, Design"
              className="category-input"
              required
            />
          </div>

          <div className="form-section">
            <h3>Initial Categories (Optional)</h3>
            <p>Add any additional categories you'll use for organizing your work:</p>
            
            {initialCategories.map((category, index) => (
              <div key={index} className="category-field">
                <input
                  type="text"
                  value={category}
                  onChange={(e) => updateCategoryField(index, e.target.value)}
                  placeholder="Category name"
                  className="category-input"
                />
                {initialCategories.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeCategoryField(index)}
                    className="remove-btn"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            
            <button
              type="button"
              onClick={addCategoryField}
              className="add-category-btn"
            >
              + Add Another Category
            </button>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-actions">
            <button
              type="submit"
              disabled={loading || !defaultCategory.trim()}
              className="complete-btn"
            >
              {loading ? 'Setting up...' : 'Complete Setup'}
            </button>
          </div>

          <div className="onboarding-info">
            <h4>What happens next?</h4>
            <ul>
              <li>✅ Your categories will be created and ready to use</li>
              <li>✅ New tasks will require a category selection</li>
              <li>✅ Invoice generation will group tasks by category</li>
              <li>✅ You can add more categories anytime in settings</li>
            </ul>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Onboarding