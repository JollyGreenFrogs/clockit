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
  const [editingCategory, setEditingCategory] = useState(null)
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    color: '',
    day_rate: ''
  })
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
          id: category.id,
          description: category.description,
          color: category.color
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

  const deleteRate = async (categoryId) => {
    if (!window.confirm('Are you sure you want to delete this category?')) {
      return
    }

    try {
      setLoading(true)
      const response = await authenticatedFetch(`/categories/${categoryId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        setResult('Category deleted successfully!')
        await loadRates()
      } else {
        const errorData = await response.json()
        setResult(`Error deleting category: ${errorData.detail || 'Unknown error'}`)
      }
    } catch {
      setResult('Error deleting category')
    } finally {
      setLoading(false)
    }
  }

  const startEditCategory = (category) => {
    setEditingCategory(category.id)
    setEditForm({
      name: category.task_type,
      description: category.description || '',
      color: category.color || '#007bff',
      day_rate: category.day_rate.toString()
    })
  }

  const cancelEdit = () => {
    setEditingCategory(null)
    setEditForm({
      name: '',
      description: '',
      color: '',
      day_rate: ''
    })
  }

  const saveEdit = async () => {
    if (!editForm.name.trim() || !editForm.day_rate) {
      setResult('Please fill in category name and day rate')
      return
    }

    try {
      setLoading(true)
      const response = await authenticatedFetch(`/categories/${editingCategory}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: editForm.name.trim(),
          description: editForm.description.trim() || null,
          color: editForm.color || '#007bff',
          day_rate: parseFloat(editForm.day_rate)
        })
      })

      if (response.ok) {
        setResult('Category updated successfully!')
        cancelEdit()
        await loadRates()
      } else {
        const errorData = await response.json()
        setResult(`Error updating category: ${errorData.detail || 'Unknown error'}`)
      }
    } catch {
      setResult('Error updating category')
    } finally {
      setLoading(false)
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
              backgroundColor: '#f8f9fa'
            }}>
              {editingCategory === rate.id ? (
                // Edit mode
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                        Category Name:
                      </label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '8px',
                          border: '1px solid #ddd',
                          borderRadius: '4px'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                        Day Rate:
                      </label>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 'bold', color: '#667eea' }}>{currencySymbol}</span>
                        <input
                          type="number"
                          value={editForm.day_rate}
                          onChange={(e) => setEditForm({ ...editForm, day_rate: e.target.value })}
                          style={{
                            flex: 1,
                            padding: '8px',
                            border: '1px solid #ddd',
                            borderRadius: '4px'
                          }}
                        />
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                        Description:
                      </label>
                      <input
                        type="text"
                        value={editForm.description}
                        onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                        placeholder="Optional description"
                        style={{
                          width: '100%',
                          padding: '8px',
                          border: '1px solid #ddd',
                          borderRadius: '4px'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                        Color:
                      </label>
                      <input
                        type="color"
                        value={editForm.color}
                        onChange={(e) => setEditForm({ ...editForm, color: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '4px',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          height: '40px'
                        }}
                      />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    <button
                      onClick={cancelEdit}
                      style={{
                        backgroundColor: '#6c757d',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '8px 16px',
                        cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={saveEdit}
                      disabled={loading}
                      style={{
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '8px 16px',
                        cursor: 'pointer'
                      }}
                    >
                      {loading ? '...' : 'Save'}
                    </button>
                  </div>
                </div>
              ) : (
                // View mode
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                  <div className="rate-info" style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <div
                        style={{
                          width: '12px',
                          height: '12px',
                          backgroundColor: rate.color || '#007bff',
                          borderRadius: '50%'
                        }}
                      />
                      <div className="rate-type" style={{
                        fontSize: '16px',
                        fontWeight: '600',
                        color: '#2c3e50'
                      }}>
                        {rate.task_type}
                      </div>
                    </div>
                    <div className="rate-values" style={{
                      fontSize: '14px',
                      color: '#7f8c8d'
                    }}>
                      {rate.currency}{rate.day_rate}/day • {rate.currency}{(rate.day_rate / 8).toFixed(2)}/hour
                    </div>
                    {rate.description && (
                      <div style={{
                        fontSize: '12px',
                        color: '#6c757d',
                        marginTop: '4px'
                      }}>
                        {rate.description}
                      </div>
                    )}
                  </div>
                  <div className="rate-actions" style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => startEditCategory(rate)}
                      style={{
                        backgroundColor: '#007bff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '8px 12px',
                        cursor: 'pointer'
                      }}
                    >
                      ✏️
                    </button>
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
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default RateConfiguration