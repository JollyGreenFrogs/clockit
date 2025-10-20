import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

function InvoiceGeneration() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const [preview, setPreview] = useState('')
  const { authenticatedFetch } = useAuth()

  const previewInvoice = async () => {
    setLoading(true)
    try {
      const response = await authenticatedFetch('/invoice/preview')
      const data = await response.json()
      
      console.log('Preview response:', response.status, data) // Debug log
      
      if (response.ok) {
        const previewText = data.preview || 'No invoice data available'
        console.log('Setting preview to:', previewText) // Debug log
        setPreview(previewText)
        setResult('Invoice preview generated successfully!')
      } else {
        setResult('Error generating preview: ' + (data.detail || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error previewing invoice:', error)
      setResult('Error generating preview')
    } finally {
      setLoading(false)
    }
  }

  const generateInvoice = async () => {
    setLoading(true)
    try {
      const response = await authenticatedFetch('/invoice/generate', {
        method: 'POST'
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `invoice-${new Date().toISOString().split('T')[0]}.csv`
        a.click()
        window.URL.revokeObjectURL(url)
        setResult('Invoice generated and downloaded successfully!')
      } else {
        const data = await response.json()
        setResult('Error generating invoice: ' + (data.detail || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error generating invoice:', error)
      setResult('Error generating invoice')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="invoice-generation">
      <div className="btn-group">
        <button 
          onClick={previewInvoice} 
          disabled={loading} 
          className="btn btn-secondary"
        >
          {loading ? <span className="loading"></span> : '👁️'} Preview Invoice
        </button>
        <button 
          onClick={generateInvoice} 
          disabled={loading} 
          className="btn btn-success"
        >
          {loading ? <span className="loading"></span> : '📄'} Generate & Export
        </button>
      </div>

      {result && (
        <div className={`alert ${result.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {result}
        </div>
      )}

      {preview && (
        <div className="invoice-preview">
          <h4>Invoice Preview</h4>
          <div className="preview-content">
            <pre style={{ 
              background: '#f8f9fa', 
              padding: '15px', 
              borderRadius: '8px',
              fontSize: '0.9em',
              overflow: 'auto',
              maxHeight: '300px'
            }}>
              {preview}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

export default InvoiceGeneration