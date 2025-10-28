#!/bin/bash
set -e

echo "🚀 Starting ClockIt Backend..."

# Generate secrets if they don't exist (for new deployments)
SECRETS_FILE="/app/data/.secrets"
if [ ! -f "$SECRETS_FILE" ]; then
    echo "🔐 Generating application secrets..."
    
    # Generate secure secrets
    SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')
    JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')
    
    # Save to persistent volume (not in image!)
    echo "SECRET_KEY=$SECRET_KEY" > "$SECRETS_FILE"
    echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> "$SECRETS_FILE"
    
    # Secure permissions
    chmod 600 "$SECRETS_FILE"
    
    echo "✅ Secrets generated and saved to persistent storage"
else
    echo "🔐 Using existing secrets from persistent storage"
fi

# Load secrets into environment
if [ -f "$SECRETS_FILE" ]; then
    export $(grep -v '^#' "$SECRETS_FILE" | xargs)
fi

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