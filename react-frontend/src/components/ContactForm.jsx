import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'

function ContactForm({ onClose }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    type: 'general',
    priority: 'medium',
    description: '',
    steps_to_reproduce: '',
    expected_behavior: '',
    actual_behavior: '',
    browser_info: navigator.userAgent || 'Unknown'
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const { authenticatedFetch } = useAuth()

  const contactTypes = [
    { value: 'bug_report', label: '🐛 Bug Report' },
    { value: 'feature_request', label: '💡 Feature Request' },
    { value: 'general', label: '💬 General Inquiry' },
    { value: 'support', label: '🛠️ Technical Support' },
    { value: 'feedback', label: '📝 Feedback' }
  ]

  const priorities = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'critical', label: 'Critical' }
  ]

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.name || !formData.email || !formData.subject || !formData.description) {
      setResult('Please fill in all required fields')
      return
    }

    setLoading(true)
    try {
      const response = await authenticatedFetch('/contact', {
        method: 'POST',
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        setResult('Thank you! Your message has been sent successfully.')
        // Reset form after successful submission
        setTimeout(() => {
          setFormData({
            name: '',
            email: '',
            subject: '',
            type: 'general',
            priority: 'medium',
            description: '',
            steps_to_reproduce: '',
            expected_behavior: '',
            actual_behavior: '',
            browser_info: navigator.userAgent || 'Unknown'
          })
          onClose && onClose()
        }, 2000)
      } else {
        const errorData = await response.json()
        setResult(`Error: ${errorData.detail || 'Failed to send message'}`)
      }
    } catch (error) {
      setResult('Error: Failed to send message. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const isBugReport = formData.type === 'bug_report'

  return (
    <div className="contact-form-overlay">
      <div className="contact-form-modal">
        <div className="contact-form-header">
          <h3>📧 Contact Us</h3>
          <button onClick={onClose} className="close-button">✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="contact-form">
          <div className="form-row">
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Your full name"
                required
              />
            </div>
            <div className="form-group">
              <label>Email *</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="your.email@example.com"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Type *</label>
              <select
                name="type"
                value={formData.type}
                onChange={handleInputChange}
                required
              >
                {contactTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleInputChange}
              >
                {priorities.map(priority => (
                  <option key={priority.value} value={priority.value}>
                    {priority.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Subject *</label>
            <input
              type="text"
              name="subject"
              value={formData.subject}
              onChange={handleInputChange}
              placeholder={isBugReport ? "Brief description of the bug" : "Brief description of your inquiry"}
              required
            />
          </div>

          <div className="form-group">
            <label>
              {isBugReport ? 'Bug Description *' : 'Description *'}
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder={isBugReport ? 
                "Describe what went wrong and when it happens..." : 
                "Please provide details about your inquiry..."
              }
              rows="4"
              required
            />
          </div>

          {isBugReport && (
            <>
              <div className="form-group">
                <label>Steps to Reproduce</label>
                <textarea
                  name="steps_to_reproduce"
                  value={formData.steps_to_reproduce}
                  onChange={handleInputChange}
                  placeholder="1. Go to...&#10;2. Click on...&#10;3. Expected vs actual result..."
                  rows="3"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Expected Behavior</label>
                  <textarea
                    name="expected_behavior"
                    value={formData.expected_behavior}
                    onChange={handleInputChange}
                    placeholder="What should have happened?"
                    rows="2"
                  />
                </div>
                <div className="form-group">
                  <label>Actual Behavior</label>
                  <textarea
                    name="actual_behavior"
                    value={formData.actual_behavior}
                    onChange={handleInputChange}
                    placeholder="What actually happened?"
                    rows="2"
                  />
                </div>
              </div>
            </>
          )}

          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn">
              {loading ? <span className="loading"></span> : '📧'} Send Message
            </button>
          </div>

          {result && (
            <div className={`alert ${result.includes('Error') ? 'alert-error' : 'alert-success'}`}>
              {result}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

export default ContactForm