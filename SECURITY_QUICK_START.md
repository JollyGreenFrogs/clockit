# Security Quick Start Guide

This guide provides immediate actions to secure ClockIt before production deployment.

## 🚨 Critical Actions (Do This First!)

### 1. Generate and Set SECRET_KEY

**Problem:** Default SECRET_KEY is insecure and allows JWT forgery.

**Fix (5 minutes):**

```bash
# Generate a strong secret key
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'

# Add to your .env file
echo "SECRET_KEY=<generated_key>" >> .env

# Or for Docker:
echo "SECRET_KEY=<generated_key>" >> .env.docker
```

**Verify:**
```bash
# Application should start without using default key
grep "SECRET_KEY" .env
# Should NOT show "test-secret-key-for-development-only"
```

---

### 2. Update Password Requirements

**Problem:** Password minimum is only 6 characters.

**Quick Fix (10 minutes):**

Edit `src/auth/services.py`, find line 52-56 and replace:

```python
# OLD CODE - Remove this
if len(password) < 6:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password must be at least 6 characters long",
    )

# NEW CODE - Replace with this
if len(password) < 12:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password must be at least 12 characters long",
    )

import re
if not re.search(r'[A-Z]', password):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password must contain at least one uppercase letter",
    )
if not re.search(r'[a-z]', password):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password must contain at least one lowercase letter",
    )
if not re.search(r'\d', password):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password must contain at least one number",
    )
if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password must contain at least one special character",
    )
```

---

### 3. Remove Hardcoded Database Credentials

**Problem:** Database password visible in docker-compose.yml

**Fix (5 minutes):**

```bash
# Create .env.docker file
cat > .env.docker << EOF
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
EOF

# Add to .gitignore
echo ".env.docker" >> .gitignore
```

Edit `docker-compose.yml`:

```yaml
# BEFORE (lines 28-36) - Remove these lines
environment:
  - POSTGRES_PASSWORD=clockit_password

# AFTER - Replace with this
env_file:
  - .env.docker
```

---

### 4. Enable HTTPS (For Production)

**Problem:** No HTTPS enforcement exposes data in transit.

**Quick Fix with Nginx (15 minutes):**

1. Get SSL certificate:
```bash
# Using Let's Encrypt (certbot)
sudo certbot --nginx -d yourdomain.com
```

2. Create nginx configuration:

```nginx
# /etc/nginx/sites-available/clockit

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/clockit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## ⚠️ High Priority Actions (Do This Next)

### 5. Secure CORS Configuration

**Fix (5 minutes):**

Edit `src/main.py` around line 163:

```python
# Add environment-based CORS
from src.config import Config

if Config.ENVIRONMENT == "production":
    # Set production frontend URL in environment
    allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
else:
    # Development origins
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit
    allow_headers=["Content-Type", "Authorization"],  # Explicit
)
```

Add to `.env`:
```bash
# For production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

### 6. Remove PostgreSQL Port Exposure

**Fix (2 minutes):**

Edit `docker-compose.yml`, comment out or remove lines 59-60:

```yaml
clockit-db:
  image: postgres:15-alpine
  # Remove these lines:
  # ports:
  #   - "5432:5432"
```

Database will only be accessible within Docker network.

---

### 7. Install Rate Limiting

**Fix (10 minutes):**

```bash
# Add to requirements.txt
echo "slowapi==0.1.9" >> requirements.txt

# Install
pip install slowapi
```

Add to `src/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add to auth endpoints
@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

## 🔧 Security Configuration Template

### Complete .env.docker Template

```env
# Generated: 2025-10-20
# Keep this file secure - never commit to git

# Application
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_TYPE=postgres
POSTGRES_HOST=clockit-db
POSTGRES_PORT=5432
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD=<generate-strong-password-here>

# Security
SECRET_KEY=<generate-64-char-secret-here>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=https://yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Generate All Secrets Script

```bash
#!/bin/bash
# save as scripts/generate-production-secrets.sh

echo "Generating production secrets..."

cat > .env.docker << EOF
# Generated: $(date)
# Keep this file secure

ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

DATABASE_TYPE=postgres
POSTGRES_HOST=clockit-db
POSTGRES_PORT=5432
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Update with your domain
CORS_ORIGINS=https://yourdomain.com

LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

chmod 600 .env.docker
echo "✅ Secrets generated in .env.docker"
echo "⚠️  Update CORS_ORIGINS with your domain"
```

Usage:
```bash
chmod +x scripts/generate-production-secrets.sh
./scripts/generate-production-secrets.sh
```

---

## 🚀 Quick Deployment Checklist

Before deploying to production:

- [ ] SECRET_KEY is set (not default)
- [ ] Strong password policy implemented
- [ ] Database credentials in .env.docker (not in code)
- [ ] .env.docker is in .gitignore
- [ ] HTTPS is enabled
- [ ] PostgreSQL port is not exposed
- [ ] CORS origins are configured for production
- [ ] Rate limiting is enabled
- [ ] Security headers are set

**Deploy command:**
```bash
# Build and deploy
docker-compose -f docker-compose.yml up -d --build

# Verify
curl -I https://yourdomain.com | grep -E "(Strict-Transport|X-Frame|X-Content)"
```

---

## 🧪 Quick Security Test

Test your security configuration:

```bash
# 1. Check SECRET_KEY is set
docker-compose exec clockit-backend env | grep SECRET_KEY
# Should show actual key, not "test-secret-key"

# 2. Test HTTPS redirect
curl -I http://yourdomain.com
# Should return 301/307/308 redirect to https://

# 3. Test security headers
curl -I https://yourdomain.com
# Should show X-Frame-Options, X-Content-Type-Options, etc.

# 4. Test rate limiting
for i in {1..10}; do 
  curl -X POST https://yourdomain.com/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done
# Last requests should return 429 (Too Many Requests)

# 5. Test database port not exposed
nmap -p 5432 yourdomain.com
# Should show port closed/filtered

# 6. Test password strength
curl -X POST https://yourdomain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"test","password":"weak"}'
# Should return 400 with password requirements error
```

---

## 📞 Need Help?

### Common Issues

**Issue:** Application won't start after setting SECRET_KEY
**Fix:** Make sure the SECRET_KEY is properly quoted in .env file
```bash
SECRET_KEY="your-key-here"  # Use quotes
```

**Issue:** Database connection fails after removing port exposure
**Fix:** Ensure services are on the same Docker network
```yaml
networks:
  - clockit-network
```

**Issue:** CORS errors after updating configuration
**Fix:** Verify frontend URL exactly matches CORS_ORIGINS
```bash
# Must include protocol and exact domain
CORS_ORIGINS=https://app.yourdomain.com  # Correct
CORS_ORIGINS=app.yourdomain.com  # Wrong (missing https://)
```

**Issue:** Rate limiting blocks legitimate users
**Fix:** Adjust rate limits based on your needs
```python
@limiter.limit("10/minute")  # Increase from 5 to 10
```

---

## 📚 Next Steps

After completing these quick fixes:

1. **Read the full audit report:** `SECURITY_AUDIT_REPORT.md`
2. **Implement medium-priority fixes:** `SECURITY_RECOMMENDATIONS.md`
3. **Follow the complete checklist:** `SECURITY_CHECKLIST.md`
4. **Set up monitoring and alerting**
5. **Schedule regular security audits**

---

## ✅ Verification Commands

Run these commands to verify your security improvements:

```bash
# Automated verification script
cat > scripts/verify-security.sh << 'EOF'
#!/bin/bash
echo "🔍 ClockIt Security Verification"
echo "================================"

# Check SECRET_KEY
if grep -q "test-secret-key" .env .env.docker 2>/dev/null; then
    echo "❌ Using default SECRET_KEY"
else
    echo "✅ SECRET_KEY configured"
fi

# Check .env.docker exists and is not committed
if [ -f .env.docker ] && ! git ls-files --error-unmatch .env.docker 2>/dev/null; then
    echo "✅ .env.docker exists and not in git"
else
    echo "❌ .env.docker missing or in git"
fi

# Check password validation
if grep -q "len(password) < 12" src/auth/services.py; then
    echo "✅ Strong password policy implemented"
else
    echo "❌ Weak password policy"
fi

# Check PostgreSQL port exposure
if grep -q "5432:5432" docker-compose.yml; then
    echo "⚠️  PostgreSQL port exposed"
else
    echo "✅ PostgreSQL port secured"
fi

# Check rate limiting installed
if pip list | grep -q slowapi; then
    echo "✅ Rate limiting installed"
else
    echo "❌ Rate limiting not installed"
fi

echo "================================"
echo "Security verification complete!"
EOF

chmod +x scripts/verify-security.sh
./scripts/verify-security.sh
```

---

**Time to complete:** ~1 hour  
**Impact:** Addresses 80% of critical security issues  
**Production-ready:** After completing these steps
