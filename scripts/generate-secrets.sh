#!/bin/bash
# Generate secure secrets for ClockIt deployment
# This script creates a .env file with secure random secrets

set -e

echo "🔐 ClockIt Security Secret Generator"
echo "===================================="
echo ""

# Check if .env file already exists
if [ -f ".env" ]; then
    echo "⚠️  Warning: .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Existing .env file preserved."
        exit 0
    fi
fi

# Generate secure random secrets
echo "Generating secure random secrets..."
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# Prompt for environment
read -p "Environment (production/staging/development) [production]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-production}

# Prompt for CORS origins if production
if [ "$ENVIRONMENT" = "production" ]; then
    read -p "Enter allowed CORS origins (comma-separated, e.g., https://app.example.com): " CORS_ORIGINS
else
    CORS_ORIGINS="http://localhost:5173,http://localhost:3000"
fi

# Create .env file
cat > .env << EOF
# ClockIt Environment Configuration
# Generated on $(date)
# ⚠️  KEEP THIS FILE SECURE - DO NOT COMMIT TO VERSION CONTROL

# Application Environment
ENVIRONMENT=${ENVIRONMENT}
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Data Storage
CLOCKIT_DATA_DIR=./clockit_data

# Database Configuration
DATABASE_TYPE=postgres
POSTGRES_HOST=clockit-db
POSTGRES_PORT=5432
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD=${DB_PASSWORD}

# Authentication - CRITICAL SECURITY SETTINGS
SECRET_KEY=${SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
CORS_ORIGINS=${CORS_ORIGINS}

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

echo ""
echo "✅ Secrets generated successfully!"
echo ""
echo "📋 Summary:"
echo "  - Environment: ${ENVIRONMENT}"
echo "  - SECRET_KEY: Generated (64 bytes, URL-safe)"
echo "  - Database Password: Generated (32 bytes, URL-safe)"
echo "  - CORS Origins: ${CORS_ORIGINS}"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "  1. The .env file has been created with secure random secrets"
echo "  2. NEVER commit the .env file to version control"
echo "  3. Keep backups of your secrets in a secure location"
echo "  4. Rotate secrets regularly (every 90 days recommended)"
echo "  5. Use different secrets for each environment"
echo ""
echo "🔒 File permissions set to 600 (owner read/write only)"
chmod 600 .env

echo ""
echo "Next steps:"
echo "  1. Review the .env file: cat .env"
echo "  2. Backup your secrets securely"
echo "  3. Start your application: docker-compose up -d"
echo ""
