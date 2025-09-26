#!/bin/bash

# ClockIt Desktop Launcher for WSL
# This script launches the Electron desktop application with WSL-compatible settings

echo "🚀 Starting ClockIt Desktop Application..."
echo "📍 Running in WSL-compatible mode"

# Set WSL-specific environment variables
export DISPLAY=:0
export LIBGL_ALWAYS_INDIRECT=1

# Change to the electron directory
cd "$(dirname "$0")/electron"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if backend exists
if [ ! -f "backend/clockit" ]; then
    echo "❌ Backend executable not found!"
    echo "📝 Please build the backend first by running: python -m PyInstaller --clean clockit.spec"
    echo "📝 Then copy dist/clockit to electron/backend/"
    exit 1
fi

echo "🖥️ Launching desktop application..."
echo "⚠️  Note: WSL graphics may show some warnings, but the app should work"

# Launch Electron with WSL-compatible options
npm start

echo "👋 ClockIt Desktop Application closed"
