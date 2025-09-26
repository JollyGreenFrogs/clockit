const { app, BrowserWindow, shell, Menu, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');

// Create custom temp directory to avoid /tmp permission issues
const customTempDir = path.join(os.homedir(), '.clockit-temp');
if (!fs.existsSync(customTempDir)) {
    fs.mkdirSync(customTempDir, { recursive: true, mode: 0o755 });
}

// Set environment variables for temp directory
process.env.TMPDIR = customTempDir;
process.env.TMP = customTempDir;
process.env.TEMP = customTempDir;

// Disable GPU acceleration for WSL compatibility
app.disableHardwareAcceleration();

// Add command line switches for better WSL support and fix shared memory issues
app.commandLine.appendSwitch('--no-sandbox');
app.commandLine.appendSwitch('--disable-gpu');
app.commandLine.appendSwitch('--disable-gpu-sandbox');
app.commandLine.appendSwitch('--disable-software-rasterizer');
app.commandLine.appendSwitch('--disable-dev-shm-usage');
app.commandLine.appendSwitch('--disable-extensions');
app.commandLine.appendSwitch('--disable-background-timer-throttling');
app.commandLine.appendSwitch('--disable-backgrounding-occluded-windows');
app.commandLine.appendSwitch('--disable-renderer-backgrounding');
// Fix shared memory issues in WSL/Linux environments  
app.commandLine.appendSwitch('--disable-shared-memory');
app.commandLine.appendSwitch('--disable-setuid-sandbox');
app.commandLine.appendSwitch('--no-first-run');
app.commandLine.appendSwitch('--no-default-browser-check');
// Use alternative temporary directory to avoid /tmp permission issues
app.commandLine.appendSwitch('--user-data-dir', path.join(os.homedir(), '.clockit-temp'));
app.commandLine.appendSwitch('--disk-cache-dir', path.join(customTempDir, 'cache'));
app.commandLine.appendSwitch('--log-file', path.join(customTempDir, 'debug.log'));

class ClockItApp {
    constructor() {
        this.mainWindow = null;
        this.backendProcess = null;
        this.serverPort = 8000;
        this.serverUrl = `http://localhost:${this.serverPort}`;
        this.isDev = process.argv.includes('--dev');
        this.isShuttingDown = false;
        
        // Set up app event handlers
        this.setupAppHandlers();
    }

    setupAppHandlers() {
        app.whenReady().then(() => {
            this.createMainWindow();
            this.startBackendServer();
            this.setupMenu();
            
            app.on('activate', () => {
                if (BrowserWindow.getAllWindows().length === 0) {
                    this.createMainWindow();
                }
            });
        });

        app.on('window-all-closed', () => {
            this.cleanup();
            if (process.platform !== 'darwin') {
                app.quit();
            }
        });

        app.on('before-quit', () => {
            this.cleanup();
        });
    }

    createMainWindow() {
        this.mainWindow = new BrowserWindow({
            width: 1400,
            height: 900,
            minWidth: 800,
            minHeight: 600,
            icon: path.join(__dirname, 'assets', 'icon.png'),
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                enableRemoteModule: false,
                preload: path.join(__dirname, 'preload.js'),
                webSecurity: false,  // For WSL compatibility
                experimentalFeatures: false
            },
            show: false,
            titleBarStyle: 'default',
            autoHideMenuBar: false
        });

        // Show window when ready to prevent visual flash
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
            
            if (this.isDev) {
                this.mainWindow.webContents.openDevTools();
            }
        });

        // Handle external links
        this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
            shell.openExternal(url);
            return { action: 'deny' };
        });

        // Load the application
        this.loadApplication();

        // Handle window closed
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });
    }

    async loadApplication() {
        // Show loading page first
        const loadingHtml = this.createLoadingPage();
        this.mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(loadingHtml)}`);
        
        // Wait for backend to start, then load the app
        this.waitForBackend();
    }

    createLoadingPage() {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>ClockIt - Loading</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    flex-direction: column;
                }
                .logo {
                    font-size: 4em;
                    margin-bottom: 20px;
                }
                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid rgba(255,255,255,0.3);
                    border-top: 4px solid white;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 20px;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .status {
                    font-size: 1.2em;
                    margin: 10px;
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="logo">⏰</div>
            <h1>ClockIt</h1>
            <h3>Professional Time Tracker</h3>
            <div class="spinner"></div>
            <div class="status">Starting application...</div>
            <div class="status" style="font-size: 0.9em; opacity: 0.7;">This may take a moment on first launch</div>
        </body>
        </html>
        `;
    }

    startBackendServer() {
        try {
            // Determine the backend executable path
            const backendPath = this.getBackendPath();
            
            if (!fs.existsSync(backendPath)) {
                this.showError('Backend executable not found', `Could not find backend at: ${backendPath}`);
                return;
            }

            console.log(`Starting backend: ${backendPath}`);
            
            this.backendProcess = spawn(backendPath, [], {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: path.join(__dirname, 'backend'), // Set working directory to backend folder
                env: {
                    ...process.env,
                    CLOCKIT_DESKTOP_MODE: 'true',
                    CLOCKIT_DATA_DIR: this.getDataDirectory()
                }
            });

            // Capture backend output for debugging
            if (this.backendProcess.stdout) {
                this.backendProcess.stdout.on('data', (data) => {
                    const output = data.toString();
                    console.log('Backend stdout:', output);
                    
                    // Look for port information in the output
                    const portMatch = output.match(/Server will be available at: http:\/\/localhost:(\d+)/);
                    if (portMatch) {
                        const detectedPort = parseInt(portMatch[1]);
                        if (detectedPort !== this.serverPort) {
                            console.log(`Port changed from ${this.serverPort} to ${detectedPort}`);
                            this.serverPort = detectedPort;
                            this.serverUrl = `http://localhost:${this.serverPort}`;
                        }
                    }
                });
            }

            if (this.backendProcess.stderr) {
                this.backendProcess.stderr.on('data', (data) => {
                    const error = data.toString();
                    console.error('Backend stderr:', error);
                    
                    // Don't show shared memory errors as they're non-critical
                    if (!error.includes('shared memory') && !error.includes('platform_shared_memory')) {
                        // Only show critical errors
                        if (error.includes('ERROR') && !error.includes('Chromium')) {
                            this.showError('Backend Error', `Backend reported an error: ${error}`);
                        }
                    }
                });
            }

            this.backendProcess.on('error', (error) => {
                console.error('Backend process error:', error);
                this.showError('Backend Error', `Failed to start backend: ${error.message}`);
            });

            this.backendProcess.on('exit', (code, signal) => {
                console.log(`Backend process exited with code ${code}, signal ${signal}`);
                if (code !== 0 && code !== null && this.mainWindow && !this.isShuttingDown) {
                    this.showError('Backend Crashed', 
                        `The backend server has stopped unexpectedly.\n\n` +
                        `Exit code: ${code}\n` +
                        `Signal: ${signal || 'None'}\n\n` +
                        `Please check the console output for more details.`
                    );
                }
                this.backendProcess = null;
            });

        } catch (error) {
            console.error('Failed to start backend:', error);
            this.showError('Startup Error', `Failed to start application: ${error.message}`);
        }
    }

    getBackendPath() {
        if (this.isDev) {
            // Development mode - use Python script
            return path.join(__dirname, '..', 'src', 'clockit_app.py');
        } else {
            // Production mode - use bundled executable
            const platform = os.platform();
            const backendDir = path.join(__dirname, 'backend');
            
            if (platform === 'win32') {
                return path.join(backendDir, 'clockit.exe');
            } else {
                return path.join(backendDir, 'clockit');
            }
        }
    }

    getDataDirectory() {
        // Store data in user's app data directory
        const userDataPath = app.getPath('userData');
        const dataDir = path.join(userDataPath, 'clockit_data');
        
        // Ensure directory exists
        if (!fs.existsSync(dataDir)) {
            fs.mkdirSync(dataDir, { recursive: true });
        }
        
        return dataDir;
    }

    async waitForBackend() {
        const maxAttempts = 120; // 2 minutes timeout - increased for slower systems
        let attempts = 0;
        let lastError = null;

        const checkServer = async () => {
            try {
                console.log(`Checking server (attempt ${attempts + 1}/${maxAttempts})...`);
                
                // Try connecting to the server with a longer timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
                
                const response = await fetch(this.serverUrl, { 
                    signal: controller.signal,
                    method: 'GET',
                    headers: {
                        'User-Agent': 'ClockIt-Desktop-App'
                    }
                });
                
                clearTimeout(timeoutId);
                
                if (response.ok) {
                    console.log('Server is ready!');
                    // Server is ready, load the application
                    setTimeout(() => {
                        this.mainWindow.loadURL(this.serverUrl);
                    }, 1000); // Small delay to ensure server is fully ready
                    return;
                }
            } catch (error) {
                lastError = error;
                console.log(`Server not ready: ${error.message}`);
            }

            attempts++;
            if (attempts >= maxAttempts) {
                console.error('Server startup timeout');
                console.error('Last error:', lastError);
                this.showError('Startup Timeout', 
                    `Application failed to start within expected time.\n\n` +
                    `Please check if:\n` +
                    `- Port ${this.serverPort} is available\n` +
                    `- Backend executable is working\n` +
                    `- No firewall is blocking the connection\n\n` +
                    `Last error: ${lastError?.message || 'Unknown'}`
                );
                return;
            }

            // Try again in 1 second
            setTimeout(checkServer, 1000);
        };

        // Start checking after a brief delay to let backend start
        setTimeout(checkServer, 5000); // Increased initial delay
    }

    setupMenu() {
        const template = [
            {
                label: 'File',
                submenu: [
                    {
                        label: 'New Task',
                        accelerator: 'CmdOrCtrl+N',
                        click: () => {
                            this.mainWindow.webContents.executeJavaScript(`
                                document.getElementById('taskName')?.focus();
                            `);
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'Export Data',
                        click: () => {
                            this.exportData();
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'Exit',
                        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                        click: () => {
                            app.quit();
                        }
                    }
                ]
            },
            {
                label: 'View',
                submenu: [
                    { role: 'reload' },
                    { role: 'forceReload' },
                    { role: 'toggleDevTools' },
                    { type: 'separator' },
                    { role: 'resetZoom' },
                    { role: 'zoomIn' },
                    { role: 'zoomOut' },
                    { type: 'separator' },
                    { role: 'togglefullscreen' }
                ]
            },
            {
                label: 'Window',
                submenu: [
                    { role: 'minimize' },
                    { role: 'close' }
                ]
            },
            {
                label: 'Help',
                submenu: [
                    {
                        label: 'About ClockIt',
                        click: () => {
                            this.showAbout();
                        }
                    },
                    {
                        label: 'Show Data Directory',
                        click: () => {
                            shell.openPath(this.getDataDirectory());
                        }
                    }
                ]
            }
        ];

        const menu = Menu.buildFromTemplate(template);
        Menu.setApplicationMenu(menu);
    }

    showError(title, message) {
        dialog.showErrorBox(title, message);
    }

    showAbout() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'About ClockIt',
            message: 'ClockIt Time Tracker',
            detail: 'Professional time tracking and invoice generation application.\n\nVersion: 1.0.0\nBuilt with Electron and Python'
        });
    }

    async exportData() {
        const result = await dialog.showSaveDialog(this.mainWindow, {
            title: 'Export ClockIt Data',
            defaultPath: `clockit-export-${new Date().toISOString().split('T')[0]}.zip`,
            filters: [
                { name: 'ZIP Archives', extensions: ['zip'] }
            ]
        });

        if (!result.canceled) {
            // TODO: Implement data export functionality
            dialog.showInfoBox('Export', 'Data export functionality will be implemented soon.');
        }
    }

    cleanup() {
        this.isShuttingDown = true;
        if (this.backendProcess) {
            console.log('Stopping backend process...');
            this.backendProcess.kill('SIGTERM');
            this.backendProcess = null;
        }
    }
}

// Create and start the application
new ClockItApp();
