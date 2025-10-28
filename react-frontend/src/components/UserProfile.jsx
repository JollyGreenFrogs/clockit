import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import PasswordChange from './PasswordChange'

function UserProfile({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('profile')
  const [userInfo, setUserInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const { authenticatedFetch, user } = useAuth()

  useEffect(() => {
    if (isOpen) {
      loadUserInfo()
    }
  }, [isOpen])

  const loadUserInfo = async () => {
    try {
      setLoading(true)
      const response = await authenticatedFetch('/auth/me')
      if (response.ok) {
        const data = await response.json()
        setUserInfo(data)
      }
    } catch (error) {
      console.error('Failed to load user info:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px', minHeight: '500px' }}>
        <div className="modal-header">
          <h2>Account Settings</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="profile-tabs">
            <button 
              className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              👤 Profile
            </button>
            <button 
              className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
              onClick={() => setActiveTab('security')}
            >
              🔒 Security
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'profile' && (
              <div className="profile-section">
                <h3>Profile Information</h3>
                
                {loading ? (
                  <div className="loading">Loading profile...</div>
                ) : userInfo ? (
                  <div className="profile-info">
                    <div className="info-grid">
                      <div className="info-item">
                        <label>Full Name:</label>
                        <span>{userInfo.full_name || 'Not set'}</span>
                      </div>
                      
                      <div className="info-item">
                        <label>Username:</label>
                        <span>{userInfo.username}</span>
                      </div>
                      
                      <div className="info-item">
                        <label>Email:</label>
                        <span>{userInfo.email}</span>
                      </div>
                      
                      <div className="info-item">
                        <label>Account Status:</label>
                        <span className={`status ${userInfo.is_active ? 'active' : 'inactive'}`}>
                          {userInfo.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      
                      <div className="info-item">
                        <label>Subscription:</label>
                        <span className="subscription">{userInfo.subscription_tier || 'Free'}</span>
                      </div>
                      
                      <div className="info-item">
                        <label>Member Since:</label>
                        <span>{new Date(userInfo.created_at).toLocaleDateString()}</span>
                      </div>
                      
                      <div className="info-item">
                        <label>Onboarding:</label>
                        <span className={`onboarding ${userInfo.onboarding_completed ? 'completed' : 'pending'}`}>
                          {userInfo.onboarding_completed ? 'Completed' : 'Pending'}
                        </span>
                      </div>
                    </div>
                    
                    <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                      <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
                        📝 Profile editing functionality will be available in a future update.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="error">Failed to load profile information</div>
                )}
              </div>
            )}

            {activeTab === 'security' && (
              <div className="security-section">
                <h3>Security Settings</h3>
                <PasswordChange />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserProfile