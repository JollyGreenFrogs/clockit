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
    loadRates()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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
      const response = await authenticatedFetch('/rates')
      const data = await response.json()
      setRates(data.rates || [])
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
    if (!taskType || !dayRate || !selectedCurrency) {
      setResult('Please fill in all fields')
      return
    }

    setLoading(true)
    try {
      const response = await authenticatedFetch('/rates', {
        method: 'POST',
        body: JSON.stringify({
          task_type: taskType,
          day_rate: parseFloat(dayRate),
          currency: selectedCurrency
        })
      })

      if (response.ok) {
        setResult('Rate set successfully!')
        setTaskType('')
        setDayRate('')
        await loadRates()
      } else {
        setResult('Error setting rate')
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
        {rates.map((rate, index) => (
          <div key={index} className="rate-item">
            <div className="rate-info">
              <div className="rate-type">{rate.task_type}</div>
              <div className="rate-values">
                {rate.currency} {rate.day_rate}/day • {rate.currency} {(rate.day_rate / 8).toFixed(2)}/hour
              </div>
            </div>
            <div className="rate-actions">
              <button 
                onClick={() => deleteRate(rate.id)}
                className="btn btn-danger btn-small"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RateConfiguration