#!/bin/bash
set -e

echo "🚀 Starting ClockIt Backend..."

# Database initialization
echo "🗄️  Initializing database..."
python scripts/init_database.py

# Check if initialization was successful
if [ $? -eq 0 ]; then
    echo "✅ Database initialization completed successfully!"
else
    echo "❌ Database initialization failed!"
    exit 1
fi

# Start the FastAPI application
echo "🌐 Starting FastAPI server..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000