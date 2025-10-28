import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import UserProfile from './UserProfile';
import './Auth.css';

const UserMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const { user, logout } = useAuth();
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
  };

  const getInitials = (name) => {
    if (!name) return user?.username?.charAt(0)?.toUpperCase() || 'U';
    
    const names = name.split(' ');
    if (names.length >= 2) {
      return (names[0].charAt(0) + names[1].charAt(0)).toUpperCase();
    }
    return name.charAt(0).toUpperCase();
  };

  return (
    <>
      <div className="user-menu" ref={menuRef}>
        <button 
          className="user-menu-button"
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
        >
          <div className="user-avatar">
            {getInitials(user?.full_name)}
          </div>
          <span className="user-name">
            {user?.full_name || user?.username || 'User'}
          </span>
          <span className="dropdown-arrow">
            {isOpen ? '▲' : '▼'}
          </span>
        </button>

        {isOpen && (
          <div className="user-menu-dropdown">
            <div className="user-menu-item" style={{ borderBottom: '1px solid #e1e5e9', marginBottom: '8px', paddingBottom: '12px' }}>
              <div style={{ fontWeight: '600', fontSize: '14px' }}>
                {user?.full_name || user?.username}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
                {user?.email}
              </div>
            </div>
            
            <button 
              className="user-menu-item"
              onClick={() => {
                setIsOpen(false);
                setShowProfile(true);
              }}
            >
              👤 Profile Settings
            </button>
            
            <button 
              className="user-menu-item"
              onClick={() => {
                setIsOpen(false);
                setShowProfile(true);
              }}
            >
              ⚙️ Account Settings
            </button>
            
            <div style={{ height: '1px', background: '#e1e5e9', margin: '8px 0' }}></div>
            
            <button 
              className="user-menu-item danger"
              onClick={handleLogout}
            >
              🚪 Sign Out
            </button>
          </div>
        )}
      </div>
      
      <UserProfile 
        isOpen={showProfile} 
        onClose={() => setShowProfile(false)} 
      />
    </>
  );
};

export default UserMenu;