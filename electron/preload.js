const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // App information
    getVersion: () => process.versions,
    
    // File operations
    showOpenDialog: () => ipcRenderer.invoke('dialog:openFile'),
    showSaveDialog: () => ipcRenderer.invoke('dialog:saveFile'),
    
    // System operations
    openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
    showItemInFolder: (path) => ipcRenderer.invoke('shell:showItemInFolder', path),
    
    // App controls
    minimize: () => ipcRenderer.invoke('window:minimize'),
    maximize: () => ipcRenderer.invoke('window:maximize'),
    close: () => ipcRenderer.invoke('window:close'),
    
    // Data operations
    exportData: () => ipcRenderer.invoke('data:export'),
    importData: () => ipcRenderer.invoke('data:import'),
    
    // Notifications
    showNotification: (title, body) => ipcRenderer.invoke('notification:show', title, body)
});

// Add desktop-specific enhancements to the web application
window.addEventListener('DOMContentLoaded', () => {
    // Add desktop-specific CSS class
    document.body.classList.add('electron-app');
    
    // Enhance the application for desktop use
    enhanceForDesktop();
});

function enhanceForDesktop() {
    // Add keyboard shortcuts info
    const style = document.createElement('style');
    style.textContent = `
        .electron-app {
            /* Desktop-specific styles */
            user-select: none; /* Prevent text selection for UI elements */
        }
        
        .electron-app input, .electron-app textarea {
            user-select: text; /* Allow text selection in inputs */
        }
        
        /* Add desktop-style scrollbars */
        .electron-app ::-webkit-scrollbar {
            width: 12px;
        }
        
        .electron-app ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        .electron-app ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 6px;
        }
        
        .electron-app ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* Desktop notification styles */
        .desktop-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 300px;
            animation: slideInRight 0.3s ease;
        }
        
        @keyframes slideInRight {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
        }
    `;
    document.head.appendChild(style);
    
    // Add desktop keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'n':
                    e.preventDefault();
                    // Focus on new task input
                    const taskInput = document.getElementById('taskName');
                    if (taskInput) taskInput.focus();
                    break;
                case ',':
                    e.preventDefault();
                    // Open settings/preferences
                    break;
                case 'r':
                    if (e.shiftKey) {
                        e.preventDefault();
                        window.location.reload();
                    }
                    break;
            }
        }
        
        // F5 refresh
        if (e.key === 'F5') {
            e.preventDefault();
            window.location.reload();
        }
    });
    
    // Add context menu enhancements
    document.addEventListener('contextmenu', (e) => {
        // You can add custom context menu items here
    });
    
    // Add desktop notifications support
    if ('Notification' in window) {
        // Request permission for notifications
        Notification.requestPermission();
    }
}

// Desktop-specific utility functions
window.desktopUtils = {
    showNotification: (title, message, options = {}) => {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: options.icon || '/favicon.ico',
                ...options
            });
        } else {
            // Fallback to in-app notification
            showInAppNotification(title, message);
        }
    },
    
    openDataDirectory: () => {
        if (window.electronAPI) {
            window.electronAPI.showItemInFolder(process.env.CLOCKIT_DATA_DIR || '');
        }
    }
};

function showInAppNotification(title, message) {
    const notification = document.createElement('div');
    notification.className = 'desktop-notification';
    notification.innerHTML = `
        <strong>${title}</strong><br>
        ${message}
        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; font-size: 18px; cursor: pointer;">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}
