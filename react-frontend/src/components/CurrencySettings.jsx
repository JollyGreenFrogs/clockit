import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'

function CurrencySettings() {
  const [currencies, setCurrencies] = useState([])
  const [currentCurrency, setCurrentCurrency] = useState('')
  const [selectedCurrency, setSelectedCurrency] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const { authenticatedFetch } = useAuth()

  useEffect(() => {
    loadCurrencies()
    loadCurrentCurrency()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loadCurrencies = async () => {
    try {
      const response = await authenticatedFetch('/currency/available')
      const data = await response.json()
      setCurrencies(data.currencies || [])
    } catch {
      // Handle error silently
    }
  }

  const loadCurrentCurrency = async () => {
    try {
      const response = await authenticatedFetch('/currency')
      const data = await response.json()
      // Handle both object format {code, symbol, name} and string format
      const currencyCode = data.currency?.code || data.currency || 'USD'
      setCurrentCurrency(currencyCode)
      setSelectedCurrency(currencyCode)
    } catch {
      // Handle error silently
    }
  }

  const applyCurrency = async () => {
    if (!selectedCurrency) {
      setResult('Please select a currency')
      return
    }

    setLoading(true)
    try {
      const response = await authenticatedFetch('/currency', {
        method: 'POST',
        body: JSON.stringify({
          currency: selectedCurrency
        })
      })

      if (response.ok) {
        setResult('Currency updated successfully!')
        setCurrentCurrency(selectedCurrency)
      } else {
        setResult('Error updating currency')
      }
    } catch {
      setResult('Error updating currency')
    } finally {
      setLoading(false)
    }
  }

  const getCurrencyName = (code) => {
    const currency = currencies.find(c => c.code === code)
    return currency ? currency.name : code
  }

  return (
    <div className="currency-settings">
      <div className="form-grid">
        <div className="form-row">
          <label>Currency:</label>
          <select 
            value={selectedCurrency} 
            onChange={(e) => setSelectedCurrency(e.target.value)}
          >
            <option value="">Select currency...</option>
            {currencies.map(currency => (
              <option key={currency.code} value={currency.code}>
                {currency.code} - {currency.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="btn-group">
        <button onClick={applyCurrency} disabled={loading} className="btn">
          {loading ? <span className="loading"></span> : '💾'} Set Currency
        </button>
        <button onClick={loadCurrentCurrency} className="btn btn-secondary">
          🔄 Refresh
        </button>
      </div>

      {result && (
        <div className={`alert ${result.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {result}
        </div>
      )}

      {currentCurrency && (
        <div className="alert alert-success">
          <strong>Current Currency:</strong> {currentCurrency} - {getCurrencyName(currentCurrency)}
        </div>
      )}
    </div>
  )
}

export default CurrencySettings