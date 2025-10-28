import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'

function RateConfiguration() {
  const [currencies, setCurrencies] = useState([])
  const [rates, setRates] = useState([])
  const [selectedCurrency, setSelectedCurrency] = useState('')
  const [currencySymbol, setCurrencySymbol] = useState('$')
  const [taskType, setTaskType] = useState('')
  const [dayRate, setDayRate] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const { authenticatedFetch } = useAuth()

  useEffect(() => {
    loadCurrencies()
    loadCurrentCurrency()
    loadRates()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loadCurrentCurrency = async () => {
    try {
      const response = await authenticatedFetch('/currency')
      if (response.ok) {
        const data = await response.json()
        if (data.currency) {
          setSelectedCurrency(data.currency.code)
          setCurrencySymbol(data.currency.symbol)
        }
      }
    } catch {
      // Handle error silently
    }
  }

  const loadCurrencies = async () => {
    try {
      const response = await authenticatedFetch('/currencies')
      
      // Check if response is OK
      if (!response.ok) {
        return
      }
      
      // Check content type
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        return
      }
      
      const data = await response.json()
      setCurrencies(data.currencies || [])
    } catch {
      // No fallback currencies - show error state instead
      setCurrencies([])
    }
  }

  const loadRates = async () => {
    try {
      // Load categories instead of rates since that's where day rates are stored
      const categoriesResponse = await authenticatedFetch('/categories')
      
      if (!categoriesResponse.ok) {
        return
      }
      
      const categoriesData = await categoriesResponse.json()
      
      // Check if the response is an error object
      if (categoriesData.detail) {
        return
      }
      
      // Try to load currency, but don't fail if it doesn't work
      let symbol = '$' // Default fallback
      try {
        const currencyResponse = await authenticatedFetch('/currency')
        if (currencyResponse.ok) {
          const currencyData = await currencyResponse.json()
          const currentCurrency = currencyData.currency
          if (currentCurrency && currentCurrency.symbol) {
            symbol = currentCurrency.symbol
          }
        }
      } catch {
        // Handle currency error silently
      }
      
      // Convert categories to rates format for display - show all categories
      const ratesArray = (categoriesData.categories || [])
        .map(category => ({
          task_type: category.name,
          day_rate: category.day_rate || 0,
          currency: symbol,
          id: category.id
        }))
      
      setRates(ratesArray)
    } catch {
      // Handle error silently
    }
  }

  const handleCurrencyChange = (value) => {
    setSelectedCurrency(value)
    const currency = currencies.find(c => c.code === value)
    if (currency) {
      setCurrencySymbol(currency.symbol)
    }
  }

  const setRate = async () => {
    if (!taskType || !dayRate) {
      setResult('Please fill in task type and day rate')
      return
    }

    setLoading(true)
    try {
      const response = await authenticatedFetch('/categories', {
        method: 'POST',
        body: JSON.stringify({
          task_type: taskType,
          day_rate: parseFloat(dayRate)
        })
      })

      if (response.ok) {
        setResult('Category created successfully!')
        setTaskType('')
        setDayRate('')
        await loadRates()
      } else {
        const errorData = await response.json()
        setResult(`Error creating category: ${errorData.detail || 'Unknown error'}`)
      }
    } catch {
      setResult('Error creating category')
    } finally {
      setLoading(false)
    }
  }

  const deleteRate = async () => {
    try {
      // For now, let's just reload the data since we don't have a delete endpoint yet
      // TODO: Implement category deletion endpoint
      await loadRates()
    } catch {
      // Handle error silently
    }
  }

  return (
    <div className="rate-configuration">
      <div className="form-grid">
        <div className="form-row">
          <label>Currency:</label>
          <select 
            value={selectedCurrency} 
            onChange={(e) => handleCurrencyChange(e.target.value)}
          >
            <option value="">Select currency...</option>
            {currencies.map(currency => (
              <option key={currency.code} value={currency.code}>
                {currency.code} - {currency.name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label>Category Name:</label>
          <input
            type="text"
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
            placeholder="e.g., Design, Development"
          />
        </div>
        <div className="form-row">
          <label>Day Rate:</label>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{ fontWeight: 'bold', color: '#667eea' }}>{currencySymbol}</span>
            <input
              type="number"
              value={dayRate}
              onChange={(e) => setDayRate(e.target.value)}
              step="1"
              min="0"
              placeholder="e.g., 400"
              style={{ flex: 1 }}
            />
          </div>
        </div>
      </div>

      <div className="btn-group">
        <button onClick={setRate} disabled={loading} className="btn">
          {loading ? <span className="loading"></span> : '💾'} Create Category
        </button>
        <button onClick={loadRates} className="btn btn-secondary">
          🔄 Refresh Categories
        </button>
      </div>

      {result && (
        <div className={`alert ${result.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {result}
        </div>
      )}

      <div className="rates-list">
        {rates.length === 0 ? (
          <div className="no-rates">
            <p>No categories with rates configured yet. Create your first category above!</p>
          </div>
        ) : (
          rates.map((rate, index) => (
            <div key={index} className="rate-item" style={{
              border: '1px solid #e1e5e9',
              borderRadius: '8px',
              padding: '16px',
              margin: '12px 0',
              backgroundColor: '#f8f9fa',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div className="rate-info" style={{ flex: 1 }}>
                <div className="rate-type" style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  color: '#2c3e50',
                  marginBottom: '4px'
                }}>
                  {rate.task_type}
                </div>
                <div className="rate-values" style={{
                  fontSize: '14px',
                  color: '#7f8c8d'
                }}>
                  {rate.currency}{rate.day_rate}/day • {rate.currency}{(rate.day_rate / 8).toFixed(2)}/hour
                </div>
              </div>
              <div className="rate-actions">
                <button 
                  onClick={() => deleteRate(rate.id)}
                  className="btn btn-danger btn-small"
                  style={{
                    backgroundColor: '#e74c3c',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '8px 12px',
                    cursor: 'pointer'
                  }}
                >
                  🗑️
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default RateConfiguration