#!/bin/bash

# ClockIt Production Secrets Generator
# Generate secure secrets for production deployment

echo "🔐 ClockIt Production Secrets Generator"
echo "======================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required to generate secure secrets"
    exit 1
fi

echo "Generating secure secrets for production deployment..."
echo

echo "🔑 SECRET_KEY (64 characters):"
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
echo "$SECRET_KEY"
echo

echo "🔑 JWT_SECRET_KEY (64 characters):"
JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
echo "$JWT_SECRET_KEY"
echo

echo "🔑 POSTGRES_PASSWORD (32 characters):"
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
echo "$POSTGRES_PASSWORD"
echo

echo "📋 Copy these values to your .env.prod file:"
echo "============================================="
echo "SECRET_KEY=$SECRET_KEY"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo

echo "⚠️  SECURITY REMINDER:"
echo "- Keep these secrets secure and never commit them to git"
echo "- Store them safely in your password manager"
echo "- Use different secrets for each environment (dev/staging/prod)"
echo "- Regenerate secrets if they are ever compromised"
echo

# Optionally update .env.prod file
read -p "Would you like to automatically update .env.prod with these secrets? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ENV_PROD_FILE="$(dirname "$0")/.env.prod"
    if [ -f "$ENV_PROD_FILE" ]; then
        # Create backup
        cp "$ENV_PROD_FILE" "$ENV_PROD_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Update secrets
        sed -i "s/SECRET_KEY=CHANGE_ME_GENERATE_SECURE_SECRET_KEY_64_CHARS_MIN/SECRET_KEY=$SECRET_KEY/" "$ENV_PROD_FILE"
        sed -i "s/JWT_SECRET_KEY=CHANGE_ME_GENERATE_SECURE_JWT_SECRET_KEY_64_CHARS_MIN/JWT_SECRET_KEY=$JWT_SECRET_KEY/" "$ENV_PROD_FILE"
        sed -i "s/POSTGRES_PASSWORD=CHANGE_ME_SECURE_POSTGRES_PASSWORD_HERE/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" "$ENV_PROD_FILE"
        
        echo "✅ Updated .env.prod with generated secrets"
        echo "📁 Backup saved as .env.prod.backup.$(date +%Y%m%d_%H%M%S)"
        echo
        echo "⚠️  IMPORTANT: Please review and update the following in .env.prod:"
        echo "- CORS_ORIGINS: Update with your actual domain(s)"
        echo "- Other environment-specific settings as needed"
    else
        echo "❌ .env.prod file not found"
        echo "Please run this script from the project root directory"
    fi
else
    echo "Manual update required - copy the secrets above to your .env.prod file"
fi