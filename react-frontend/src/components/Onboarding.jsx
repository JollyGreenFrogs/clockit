import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import './Onboarding.css'

function Onboarding() {
  const [defaultCategory, setDefaultCategory] = useState('')
  const [defaultRate, setDefaultRate] = useState('')
  const [initialCategories, setInitialCategories] = useState([{ name: '', rate: '' }])
  const [currencyCode, setCurrencyCode] = useState('USD')
  const [currencySymbol, setCurrencySymbol] = useState('$')
  const [currencyName, setCurrencyName] = useState('US Dollar')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const { authenticatedFetch, user, refreshUser } = useAuth()

  const commonCurrencies = [
    { code: 'USD', symbol: '$', name: 'US Dollar' },
    { code: 'EUR', symbol: '€', name: 'Euro' },
    { code: 'GBP', symbol: '£', name: 'British Pound' },
    { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
    { code: 'AUD', symbol: 'A$', name: 'Australian Dollar' },
    { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
    { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc' },
    { code: 'SEK', symbol: 'kr', name: 'Swedish Krona' },
    { code: 'NOK', symbol: 'kr', name: 'Norwegian Krone' },
    { code: 'DKK', symbol: 'kr', name: 'Danish Krone' }
  ]

  const handleCurrencyChange = (e) => {
    const selectedCode = e.target.value
    const currency = commonCurrencies.find(c => c.code === selectedCode)
    if (currency) {
      setCurrencyCode(currency.code)
      setCurrencySymbol(currency.symbol)
      setCurrencyName(currency.name)
    }
  }

  const addCategoryField = () => {
    setInitialCategories([...initialCategories, { name: '', rate: '' }])
  }

  const removeCategoryField = (index) => {
    setInitialCategories(initialCategories.filter((_, i) => i !== index))
  }

  const updateCategoryField = (index, field, value) => {
    const updated = [...initialCategories]
    updated[index][field] = value
    setInitialCategories(updated)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!defaultCategory.trim()) {
      setError('Default category is required')
      return
    }

    if (!defaultRate || parseFloat(defaultRate) <= 0) {
      setError('Default rate must be a positive number')
      return
    }

    // Validate all categories have rates
    const validCategories = initialCategories.filter(cat => cat.name.trim())
    for (const cat of validCategories) {
      if (!cat.rate || parseFloat(cat.rate) <= 0) {
        setError(`Rate for "${cat.name}" must be a positive number`)
        return
      }
    }

    setLoading(true)
    setError('')

    try {
      // Build rates object including default category
      const rates = { [defaultCategory.trim()]: parseFloat(defaultRate) }
      validCategories.forEach(cat => {
        if (cat.name.trim()) {
          rates[cat.name.trim()] = parseFloat(cat.rate)
        }
      })

      // Build categories array (without default category since it's separate)
      const categories = validCategories
        .map(cat => cat.name.trim())
        .filter(name => name !== defaultCategory.trim())

      const response = await authenticatedFetch('/onboarding/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          default_category: defaultCategory.trim(),
          categories: categories,
          rates: rates,
          currency_code: currencyCode,
          currency_symbol: currencySymbol,
          currency_name: currencyName
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
            <h3>Currency Settings</h3>
            <p>Choose your default currency for rates and invoicing:</p>
            <div className="currency-selection">
              <select
                value={currencyCode}
                onChange={handleCurrencyChange}
                className="currency-select"
                required
              >
                {commonCurrencies.map(currency => (
                  <option key={currency.code} value={currency.code}>
                    {currency.code} ({currency.symbol}) - {currency.name}
                  </option>
                ))}
              </select>
              <div className="currency-preview">
                Selected: <strong>{currencySymbol}{defaultRate || '0.00'}</strong> per day
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Default Task Category & Rate</h3>
            <p>This will be your primary category for new tasks and invoicing:</p>
            <div className="category-rate-row">
              <input
                type="text"
                value={defaultCategory}
                onChange={(e) => setDefaultCategory(e.target.value)}
                placeholder="e.g., Development, Consulting, Design"
                className="category-input"
                required
              />
              <div className="rate-input-wrapper">
                <span className="currency-prefix">{currencySymbol}</span>
                <input
                  type="number"
                  value={defaultRate}
                  onChange={(e) => setDefaultRate(e.target.value)}
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                  className="rate-input"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Additional Categories (Optional)</h3>
            <p>Add any additional categories you'll use for organizing your work:</p>
            
            {initialCategories.map((category, index) => (
              <div key={index} className="category-field">
                <div className="category-rate-row">
                  <input
                    type="text"
                    value={category.name}
                    onChange={(e) => updateCategoryField(index, 'name', e.target.value)}
                    placeholder="Category name"
                    className="category-input"
                  />
                  <div className="rate-input-wrapper">
                    <span className="currency-prefix">{currencySymbol}</span>
                    <input
                      type="number"
                      value={category.rate}
                      onChange={(e) => updateCategoryField(index, 'rate', e.target.value)}
                      placeholder="0.00"
                      min="0"
                      step="0.01"
                      className="rate-input"
                    />
                  </div>
                </div>
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

          <div className="info-section">
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