import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

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
    } catch (error) {
      console.error('Error loading current currency:', error)
    }
  }

  const loadCurrencies = async () => {
    try {
      const response = await authenticatedFetch('/currencies')
      
      // Check if response is OK
      if (!response.ok) {
        console.error('Currency API error:', response.status, response.statusText)
        return
      }
      
      // Check content type
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        console.error('Invalid content type:', contentType)
        const text = await response.text()
        console.error('Response body:', text)
        return
      }
      
      const data = await response.json()
      setCurrencies(data.currencies || [])
    } catch (error) {
      console.error('Error loading currencies:', error)
      // No fallback currencies - show error state instead
      setCurrencies([])
    }
  }

  const loadRates = async () => {
    try {
      // Load rates first
      const ratesResponse = await authenticatedFetch('/rates')
      
      if (!ratesResponse.ok) {
        console.error('Rates API error:', ratesResponse.status, ratesResponse.statusText)
        return
      }
      
      const ratesData = await ratesResponse.json()
      
      // Check if the response is an error object
      if (ratesData.detail) {
        console.error('Rates API returned error:', ratesData.detail)
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
      } catch (currencyError) {
        console.warn('Currency loading failed, using default $:', currencyError)
      }
      
      // Backend returns rates directly as an object, convert to array for display
      const ratesArray = Object.entries(ratesData).map(([taskType, dayRate]) => ({
        task_type: taskType,  // Use underscore to match expected format
        day_rate: dayRate,
        currency: symbol, // Use current user's currency symbol or fallback
        id: taskType // Use task type as ID for deletion
      }))
      
      setRates(ratesArray)
    } catch (error) {
      console.error('Error loading rates:', error)
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
      const response = await authenticatedFetch('/rates', {
        method: 'POST',
        body: JSON.stringify({
          task_type: taskType,
          day_rate: parseFloat(dayRate)
        })
      })

      if (response.ok) {
        setResult('Rate set successfully!')
        setTaskType('')
        setDayRate('')
        await loadRates()
      } else {
        const errorData = await response.json()
        setResult(`Error setting rate: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error setting rate:', error)
      setResult('Error setting rate')
    } finally {
      setLoading(false)
    }
  }

  const deleteRate = async (rateId) => {
    try {
      await authenticatedFetch(`/rates/${rateId}`, {
        method: 'DELETE'
      })
      await loadRates()
    } catch (error) {
      console.error('Error deleting rate:', error)
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
          <label>Task Type:</label>
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
          {loading ? <span className="loading"></span> : '💾'} Set Rate
        </button>
        <button onClick={loadRates} className="btn btn-secondary">
          🔄 Refresh Rates
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
            <p>No rates configured yet. Set your first rate above!</p>
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