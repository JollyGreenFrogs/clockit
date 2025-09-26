#!/usr/bin/env python3
"""
ClockIt - Professional Time Tracker Application
Standalone executable entry point for Windows 11
"""

import os
import sys
import webbrowser
import threading
import time
import subprocess
import socket
import signal
from pathlib import Path

# Add the current directory to Python path for imports
if getattr(sys, 'frozen', False):
    # If running as PyInstaller executable
    current_dir = Path(sys.executable).parent.absolute()
else:
    # If running as Python script
    current_dir = Path(__file__).parent.absolute()

sys.path.insert(0, str(current_dir))

# Create data directory for storing config and output files in the same directory as executable
data_dir = current_dir / "clockit_data"
data_dir.mkdir(exist_ok=True)

# Set environment variable for data directory
os.environ['CLOCKIT_DATA_DIR'] = str(data_dir)

# Global variable to store the port and server
app_port = 8000
server_process = None

def find_available_port():
    """Find an available port starting from 8000"""
    global app_port
    port = 8000
    while port < 8010:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
            app_port = port
            return port
        except OSError:
            port += 1
    return 8000  # fallback

def start_server():
    """Start the FastAPI server"""
    global server_process
    try:
        import uvicorn
        from main import app
        
        print("🚀 Starting ClockIt Time Tracker...")
        print(f"📁 Data directory: {data_dir}")
        
        # Check if running in desktop mode
        desktop_mode = os.environ.get('CLOCKIT_DESKTOP_MODE', 'false').lower() == 'true'
        
        # Find an available port
        port = find_available_port()
        print(f"📍 Server will be available at: http://localhost:{port}")
        
        if not desktop_mode:
            print("🔴 Press Ctrl+C to stop the application")
        else:
            print("🖥️ Running in desktop mode")
        print()
        
        # Start the server
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=port, 
            log_level="error" if desktop_mode else "info",
            access_log=False
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Shutdown signal received...")
        graceful_shutdown()
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

def graceful_shutdown():
    """Gracefully shutdown the application"""
    print("🛑 Shutting down ClockIt...")
    print("💾 All data has been saved automatically")
    print("👋 Thank you for using ClockIt!")
    sys.exit(0)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n")
    graceful_shutdown()

def open_browser():
    """Open the browser after a delay"""
    # Don't auto-open browser in desktop mode
    desktop_mode = os.environ.get('CLOCKIT_DESKTOP_MODE', 'false').lower() == 'true'
    if desktop_mode:
        return
    
    time.sleep(2)  # Wait for server to start
    try:
        print("🌐 Opening browser...")
        url = f"http://localhost:{app_port}"
        
        # Try different methods to open browser
        if sys.platform.startswith('win'):
            os.startfile(url)
        elif sys.platform.startswith('darwin'):
            subprocess.run(["open", url])
        else:
            # Linux - try multiple options
            try:
                webbrowser.open(url)
            except:
                print(f"📌 Please manually open: {url}")
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"📌 Please manually open: http://localhost:{app_port}")

def main():
    """Main entry point"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("="*60)
    print("⏰ ClockIt - Professional Time Tracker")
    print("="*60)
    print()
    
    # Change to the application directory
    os.chdir(current_dir)
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start the server (this blocks)
    try:
        start_server()
    except KeyboardInterrupt:
        graceful_shutdown()

if __name__ == "__main__":
    main()
