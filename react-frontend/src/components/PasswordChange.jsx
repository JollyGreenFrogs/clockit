import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'

function PasswordChange() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const [showPasswords, setShowPasswords] = useState(false)

  const { authenticatedFetch } = useAuth()

  const validatePassword = (password) => {
    if (password.length < 8) {
      return "Password must be at least 8 characters long"
    }
    if (!/[A-Z]/.test(password)) {
      return "Password must contain at least one uppercase letter"
    }
    if (!/[a-z]/.test(password)) {
      return "Password must contain at least one lowercase letter"
    }
    if (!/\d/.test(password)) {
      return "Password must contain at least one number"
    }
    if (!/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password)) {
      return "Password must contain at least one special character"
    }
    return null
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    
    if (!currentPassword || !newPassword || !confirmPassword) {
      setResult('Please fill in all fields')
      return
    }

    if (newPassword !== confirmPassword) {
      setResult('New passwords do not match')
      return
    }

    const validationError = validatePassword(newPassword)
    if (validationError) {
      setResult(validationError)
      return
    }

    setLoading(true)
    try {
      const response = await authenticatedFetch('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      })

      if (response.ok) {
        setResult('Password changed successfully!')
        setCurrentPassword('')
        setNewPassword('')
        setConfirmPassword('')
      } else {
        const errorData = await response.json()
        setResult(`Error: ${errorData.detail || 'Failed to change password'}`)
      }
    } catch {
      setResult('Error changing password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="password-change">
      <h3 style={{ marginBottom: '20px', color: '#2c3e50' }}>Change Password</h3>
      
      <form onSubmit={handlePasswordChange}>
        <div className="form-grid" style={{ maxWidth: '400px' }}>
          <div className="form-row">
            <label>Current Password:</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPasswords ? "text" : "password"}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                required
                style={{ width: '100%', paddingRight: '40px' }}
              />
            </div>
          </div>

          <div className="form-row">
            <label>New Password:</label>
            <input
              type={showPasswords ? "text" : "password"}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new password"
              required
            />
          </div>

          <div className="form-row">
            <label>Confirm New Password:</label>
            <input
              type={showPasswords ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              required
            />
          </div>

          <div className="form-row">
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                checked={showPasswords}
                onChange={(e) => setShowPasswords(e.target.checked)}
              />
              Show passwords
            </label>
          </div>
        </div>

        <div className="btn-group">
          <button 
            type="submit" 
            disabled={loading} 
            className="btn"
            style={{ 
              backgroundColor: '#28a745', 
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? <span className="loading"></span> : '🔒'} Change Password
          </button>
        </div>
      </form>

      {result && (
        <div className={`alert ${result.includes('Error') || result.includes('not match') || result.includes('must') ? 'alert-error' : 'alert-success'}`}>
          {result}
        </div>
      )}

      <div className="password-requirements">
        <h4>Password Requirements:</h4>
        <ul>
          <li>At least 8 characters long</li>
          <li>At least one uppercase letter (A-Z)</li>
          <li>At least one lowercase letter (a-z)</li>
          <li>At least one number (0-9)</li>
          <li>At least one special character (!@#$%^&* etc.)</li>
        </ul>
      </div>
    </div>
  )
}

export default PasswordChange