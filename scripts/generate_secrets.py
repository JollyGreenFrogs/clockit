#!/usr/bin/env python3
"""
Generate secure secrets for ClockIt application
This script creates cryptographically secure secrets for production use
"""

import secrets
import string
import os
import sys


def generate_secret_key(length=64):
    """Generate a secure secret key using URL-safe base64 encoding"""
    return secrets.token_urlsafe(length)


def generate_database_password(length=32):
    """Generate a secure database password with mixed characters"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least one character from each category
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*")
    ]
    # Fill the rest with random characters
    for _ in range(length - 4):
        password.append(secrets.choice(alphabet))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def write_env_file(env_file_path, environment="production"):
    """Write environment file with generated secrets"""
    
    # Generate secrets
    secret_key = generate_secret_key(64)
    jwt_secret_key = generate_secret_key(64)
    postgres_password = generate_database_password(32)
    
    env_content = f"""# ClockIt Environment Configuration - {environment.upper()}
# Auto-generated on container build - DO NOT EDIT MANUALLY
# Generated at: {os.popen('date -u').read().strip()}

# Application Environment
ENVIRONMENT={environment}
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Data Storage Configuration
CLOCKIT_DATA_DIR=/app/data

# Database Configuration
DATABASE_TYPE=postgres
POSTGRES_HOST=clockit-db
POSTGRES_PORT=5432
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD={postgres_password}

# Authentication - Auto-generated secure keys
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret_key}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration (update with your domain)
CORS_ORIGINS=["http://localhost:3000","http://172.31.14.175:3000","http://10.0.27.159:3000"]

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security Settings
ENABLE_DEBUG_ENDPOINTS=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Application Features
ENABLE_SWAGGER_UI=false
ENABLE_REDOC=false
"""

    try:
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Environment file generated: {env_file_path}")
        print(f"🔐 Generated {len(secret_key)}-character SECRET_KEY")
        print(f"🔐 Generated {len(jwt_secret_key)}-character JWT_SECRET_KEY")
        print(f"🔐 Generated {len(postgres_password)}-character POSTGRES_PASSWORD")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing environment file: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) > 1:
        environment = sys.argv[1]
    else:
        environment = "production"
    
    env_file_path = f"/app/.env.{environment}"
    
    print(f"🔐 Generating secrets for {environment} environment...")
    
    if write_env_file(env_file_path, environment):
        print("🎉 Secret generation completed successfully!")
        sys.exit(0)
    else:
        print("❌ Secret generation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()