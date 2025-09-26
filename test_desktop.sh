#!/bin/bash

echo "🧪 Testing ClockIt Desktop Application"
echo "======================================"

# Kill any existing processes
pkill -f "clockit|electron" 2>/dev/null

echo "🔄 Starting desktop application..."

# Change to electron directory
cd /home/venura/scratch/clockit/electron

# Start electron with verbose output
ELECTRON_ENABLE_LOGGING=1 ./node_modules/.bin/electron . --enable-logging --log-level=0 2>&1 &

ELECTRON_PID=$!
echo "📱 Electron started with PID: $ELECTRON_PID"

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 10

# Check if backend is running
echo "🔍 Checking backend status:"
for port in 8000 8001 8002; do
    if curl -s http://localhost:$port/version >/dev/null 2>&1; then
        echo "✅ Backend found on port $port"
        curl -s http://localhost:$port/version | head -5
        break
    else
        echo "❌ Port $port: Not responding"
    fi
done

echo ""
echo "🖥️ Application should now be visible on your desktop"
echo "📋 Check the window for the ClockIt interface"
echo ""
echo "To stop: pkill -f electron"
