# Security Recommendations & Implementation Guide

This document provides detailed, actionable recommendations to address the security issues identified in the ClockIt platform security audit.

---

## Critical Priority Fixes

### 1. Fix Weak Default Secret Key

**File:** `src/auth/services.py`

**Current Code (Line 23-25):**
```python
self.secret_key = os.getenv(
    "SECRET_KEY", "your-secret-key-change-in-production"
)
```

**Recommended Fix:**
```python
self.secret_key = os.getenv("SECRET_KEY")
if not self.secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable must be set. "
        "Generate one using: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
    )
if len(self.secret_key) < 32:
    raise RuntimeError(
        "SECRET_KEY must be at least 32 characters long"
    )
```

**Additional Changes:**
Update `src/config.py` to validate secret key at startup:

```python
@classmethod
def validate(cls) -> bool:
    """Validate configuration and log warnings for missing required settings"""
    valid = True
    
    # Validate SECRET_KEY
    if not cls.SECRET_KEY:
        logger.error("SECRET_KEY must be set")
        valid = False
    elif cls.SECRET_KEY == "test-secret-key-for-development-only":
        if cls.ENVIRONMENT == "production":
            logger.error("Default SECRET_KEY cannot be used in production")
            valid = False
        else:
            logger.warning("Using default SECRET_KEY for development only")
    elif len(cls.SECRET_KEY) < 32:
        logger.error("SECRET_KEY must be at least 32 characters")
        valid = False
    
    # ... rest of validation
```

**Generate Secure Secret Key:**
```bash
# Generate a secure secret key
python -c 'import secrets; print(secrets.token_urlsafe(64))'

# Add to .env file
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" >> .env
```

---

### 2. Implement Strong Password Policy

**File:** `src/auth/services.py`

**Current Code (Line 52-56):**
```python
# Validate password strength
if len(password) < 6:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password must be at least 6 characters long",
    )
```

**Recommended Fix:**
Add a comprehensive password validation function:

```python
import re
from typing import Tuple

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements
    Returns: (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common patterns
    common_patterns = [
        r'(.)\1{2,}',  # Repeated characters (aaa, 111)
        r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            return False, "Password contains common patterns and is too predictable"
    
    # Check against common passwords (in production, use a proper list)
    common_passwords = [
        'password', 'password123', 'admin', 'admin123', 
        'qwerty', '123456', '12345678'
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password"
    
    return True, ""

# Update the create_user method
def create_user(
    self, email: str, username: str, password: str, full_name: Optional[str] = None
) -> User:
    """Create a new user account"""
    # ... existing code ...
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # ... rest of the method ...
```

**Optional: Integrate with Have I Been Pwned API:**
```python
import hashlib
import requests

def check_password_breach(password: str) -> bool:
    """
    Check if password has been exposed in data breaches
    Uses k-anonymity model - only first 5 chars of hash are sent
    """
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1_password[:5]
    suffix = sha1_password[5:]
    
    try:
        response = requests.get(
            f'https://api.pwnedpasswords.com/range/{prefix}',
            timeout=2
        )
        if response.status_code == 200:
            hashes = (line.split(':') for line in response.text.splitlines())
            return any(suffix == hash_suffix for hash_suffix, _ in hashes)
    except Exception:
        # If check fails, allow password but log the failure
        return False
    
    return False

# Add to password validation
is_breached = check_password_breach(password)
if is_breached:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This password has been exposed in data breaches. Please choose a different password"
    )
```

---

## High Priority Fixes

### 3. Implement HTTPS Enforcement and Security Headers

**File:** Create `src/middleware/security.py`

```python
"""
Security middleware for HTTP security headers and HTTPS enforcement
"""
from fastapi import Request, Response
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.config import Config


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Strict-Transport-Security (HSTS)
        if Config.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Content-Security-Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust based on frontend needs
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection (legacy, but doesn't hurt)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        
        # Remove sensitive server headers
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response


def setup_security_middleware(app):
    """Configure security middleware for the application"""
    
    # HTTPS redirect in production
    if Config.ENVIRONMENT == "production":
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
```

**Update `src/main.py`:**
```python
from .middleware.security import setup_security_middleware

# After creating app
app = FastAPI(
    title="ClockIt - Time Tracker", 
    version=get_full_version_info()["version"]
)

# Setup security middleware
setup_security_middleware(app)

# Then add CORS and other middleware
app.add_middleware(
    CORSMiddleware,
    # ... existing config
)
```

---

### 4. Fix CORS Configuration

**File:** `src/main.py`

**Current Code:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Recommended Fix:**
```python
# Update config.py to add CORS_ORIGINS per environment
# In src/config.py:
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://localhost:3000" if ENVIRONMENT == "development" 
    else ""
).split(",")

# In src/main.py:
from src.config import Config

# Determine CORS origins based on environment
if Config.ENVIRONMENT == "production":
    # In production, use explicit origins from environment
    allowed_origins = [origin.strip() for origin in Config.CORS_ORIGINS if origin.strip()]
    if not allowed_origins:
        logger.warning("No CORS origins configured for production")
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "User-Agent",
    ],  # Explicit headers
    expose_headers=["Content-Disposition"],  # For file downloads
    max_age=3600,  # Cache preflight requests for 1 hour
)
```

---

### 5. Implement Rate Limiting

**Install Dependencies:**
```bash
pip install slowapi
```

**Add to `requirements.txt`:**
```
slowapi==0.1.9
```

**Create `src/middleware/rate_limit.py`:**
```python
"""
Rate limiting middleware
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

def get_user_or_ip(request: Request):
    """Get user ID if authenticated, otherwise IP address"""
    # Try to get user from auth token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from src.auth.services import AuthService
            from src.database.connection import get_db
            
            token = auth_header.split(" ")[1]
            db = next(get_db())
            auth_service = AuthService(db)
            user = auth_service.get_current_user(token)
            if user:
                return f"user:{user.id}"
        except Exception:
            pass
    
    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"

# Create limiter instance
limiter = Limiter(key_func=get_user_or_ip)

def setup_rate_limiting(app):
    """Configure rate limiting for the application"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Update `src/main.py`:**
```python
from .middleware.rate_limit import setup_rate_limiting, limiter

# Setup rate limiting
setup_rate_limiting(app)

# Update auth endpoints with rate limits
@app.post("/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(...):
    ...

@app.post("/auth/register")
@limiter.limit("3/hour")  # 3 registrations per hour per IP
async def register(...):
    ...

# General API endpoints
@app.get("/tasks")
@limiter.limit("100/minute")  # 100 requests per minute for authenticated users
async def get_tasks(...):
    ...

@app.post("/tasks")
@limiter.limit("20/minute")  # 20 task creations per minute
async def create_task(...):
    ...
```

---

### 6. Remove Hardcoded Credentials

**File:** `docker-compose.yml`

**Create `.env.docker` file:**
```env
# Database credentials
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD=<generate-strong-password>

# Application secrets
SECRET_KEY=<generate-using-secrets.token_urlsafe(64)>
```

**Update `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  clockit-backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    env_file:
      - .env.docker  # Load from environment file
    depends_on:
      - clockit-db
    volumes:
      - clockit_data:/app/data
      - clockit_logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  clockit-db:
    image: postgres:15-alpine
    env_file:
      - .env.docker  # Load from environment file
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # Remove exposed ports - use internal networking only
    # ports:
    #   - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
```

**Update `.gitignore`:**
```
.env.docker
*.env
!.env.example
```

**Create secure password generator script:**
```bash
#!/bin/bash
# scripts/generate-secrets.sh

echo "Generating secure secrets for ClockIt..."
echo ""

SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

cat > .env.docker << EOF
# Generated on $(date)
# Keep this file secure and never commit it to version control

# Database Configuration
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD=${DB_PASSWORD}

# Application Security
SECRET_KEY=${SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Environment
ENVIRONMENT=production
DEBUG=false
EOF

echo "✅ Secrets generated and saved to .env.docker"
echo "⚠️  Keep this file secure and never commit it to version control"
```

---

## Medium Priority Fixes

### 7. Implement Input Validation and Sanitization

**Create `src/utils/validation.py`:**
```python
"""
Input validation and sanitization utilities
"""
import re
import html
from typing import Any, Optional


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input to prevent XSS"""
    if not value:
        return ""
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Limit length
    value = value[:max_length]
    
    # HTML escape
    value = html.escape(value)
    
    return value.strip()


def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format"""
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 30:
        return False, "Username must be less than 30 characters"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format"""
    if not email:
        return False, "Email is required"
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, ""


def validate_task_name(name: str) -> tuple[bool, str]:
    """Validate task name"""
    if not name or not name.strip():
        return False, "Task name cannot be empty"
    
    if len(name) > 200:
        return False, "Task name must be less than 200 characters"
    
    # Check for potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '\\', '/', ';']
    if any(char in name for char in dangerous_chars):
        return False, "Task name contains invalid characters"
    
    return True, ""


class ValidationError(Exception):
    """Custom validation error"""
    pass
```

**Update `src/schemas.py` to add validators:**
```python
from pydantic import BaseModel, validator, EmailStr, constr
from src.utils.validation import (
    sanitize_string,
    validate_username,
    validate_email,
    validate_task_name
)

class UserRegistration(BaseModel):
    email: EmailStr  # Pydantic's built-in email validation
    username: constr(min_length=3, max_length=30)  # type: ignore
    password: str
    full_name: Optional[str] = None
    
    @validator('username')
    def validate_username_format(cls, v):
        is_valid, message = validate_username(v)
        if not is_valid:
            raise ValueError(message)
        return v
    
    @validator('full_name')
    def sanitize_full_name(cls, v):
        if v:
            return sanitize_string(v, max_length=100)
        return v


class TaskCreate(BaseModel):
    name: constr(min_length=1, max_length=200)  # type: ignore
    description: Optional[str] = ""
    category: str
    
    @validator('name')
    def validate_task_name_format(cls, v):
        is_valid, message = validate_task_name(v)
        if not is_valid:
            raise ValueError(message)
        return sanitize_string(v, max_length=200)
    
    @validator('description')
    def sanitize_description(cls, v):
        if v:
            return sanitize_string(v, max_length=1000)
        return ""
```

---

### 8. Implement Comprehensive Logging

**Create `src/utils/security_logger.py`:**
```python
"""
Security-focused logging utilities
"""
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("security")


class SecurityLogger:
    """Centralized security event logging"""
    
    @staticmethod
    def log_auth_success(user_id: str, username: str, ip_address: str, user_agent: str):
        """Log successful authentication"""
        logger.info(
            "Authentication successful",
            extra={
                "event_type": "auth_success",
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_auth_failure(identifier: str, ip_address: str, reason: str):
        """Log failed authentication attempt"""
        logger.warning(
            f"Authentication failed: {reason}",
            extra={
                "event_type": "auth_failure",
                "identifier": identifier,
                "ip_address": ip_address,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_suspicious_activity(
        event_type: str,
        user_id: Optional[str],
        ip_address: str,
        details: Dict[str, Any]
    ):
        """Log suspicious activity"""
        logger.warning(
            f"Suspicious activity detected: {event_type}",
            extra={
                "event_type": "suspicious_activity",
                "activity_type": event_type,
                "user_id": user_id,
                "ip_address": ip_address,
                "details": json.dumps(details),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_access_denied(
        user_id: str,
        resource: str,
        action: str,
        ip_address: str
    ):
        """Log access denied events"""
        logger.warning(
            f"Access denied: {action} on {resource}",
            extra={
                "event_type": "access_denied",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_data_access(
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str
    ):
        """Log data access events"""
        logger.info(
            f"Data access: {action} on {resource_type}",
            extra={
                "event_type": "data_access",
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

---

### 9. Implement Session Management

**Create `src/auth/session_manager.py`:**
```python
"""
Session management with token revocation
"""
from datetime import datetime, timedelta
from typing import Optional, Set
import redis
import json
import os

class SessionManager:
    """Manage user sessions with token revocation"""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_available = True
        except Exception:
            self.redis_available = False
            self.blacklisted_tokens: Set[str] = set()  # Fallback to in-memory
    
    def revoke_token(self, token: str, expires_at: datetime):
        """Add token to blacklist"""
        if self.redis_available:
            # Calculate TTL based on token expiration
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            if ttl > 0:
                self.redis_client.setex(
                    f"blacklist:{token}",
                    ttl,
                    "1"
                )
        else:
            self.blacklisted_tokens.add(token)
    
    def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked"""
        if self.redis_available:
            return self.redis_client.exists(f"blacklist:{token}") > 0
        else:
            return token in self.blacklisted_tokens
    
    def revoke_all_user_tokens(self, user_id: str):
        """Revoke all tokens for a user"""
        if self.redis_available:
            self.redis_client.setex(
                f"user_revoked:{user_id}",
                86400,  # 24 hours
                datetime.utcnow().isoformat()
            )
    
    def get_user_revocation_time(self, user_id: str) -> Optional[datetime]:
        """Get time when user's tokens were revoked"""
        if self.redis_available:
            revoked_at = self.redis_client.get(f"user_revoked:{user_id}")
            if revoked_at:
                return datetime.fromisoformat(revoked_at)
        return None

# Usage in auth service
session_manager = SessionManager()
```

---

## Additional Security Enhancements

### 10. Implement Security Monitoring

**Create `src/monitoring/security_monitor.py`:**
```python
"""
Security monitoring and alerting
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """Monitor for security threats and anomalies"""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)
    
    def record_failed_login(self, identifier: str, ip_address: str):
        """Record failed login attempt"""
        now = datetime.utcnow()
        
        # Clean old attempts (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.failed_attempts[ip_address] = [
            timestamp for timestamp in self.failed_attempts[ip_address]
            if timestamp > cutoff
        ]
        
        # Add new attempt
        self.failed_attempts[ip_address].append(now)
        
        # Check for brute force
        if len(self.failed_attempts[ip_address]) >= 10:
            self.alert_brute_force(ip_address)
    
    def alert_brute_force(self, ip_address: str):
        """Alert on potential brute force attack"""
        logger.critical(
            f"SECURITY ALERT: Potential brute force attack from {ip_address}",
            extra={
                "alert_type": "brute_force",
                "ip_address": ip_address,
                "attempts": len(self.failed_attempts[ip_address]),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        # In production, send alert via email/Slack/PagerDuty
    
    def check_suspicious_pattern(self, user_id: str, pattern: str):
        """Check for suspicious activity patterns"""
        key = f"{user_id}:{pattern}"
        self.suspicious_patterns[key] += 1
        
        if self.suspicious_patterns[key] >= 5:
            logger.warning(
                f"Suspicious pattern detected for user {user_id}: {pattern}",
                extra={
                    "alert_type": "suspicious_pattern",
                    "user_id": user_id,
                    "pattern": pattern,
                    "count": self.suspicious_patterns[key]
                }
            )

security_monitor = SecurityMonitor()
```

---

## Deployment Security Checklist

### Production Deployment Steps:

1. **Generate Secure Secrets:**
```bash
# Run the secret generation script
chmod +x scripts/generate-secrets.sh
./scripts/generate-secrets.sh
```

2. **Enable HTTPS:**
```bash
# Use Let's Encrypt for SSL certificates
certbot --nginx -d yourdomain.com
```

3. **Configure Firewall:**
```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

4. **Database Security:**
```sql
-- Create dedicated database user with limited permissions
CREATE USER clockit_app WITH PASSWORD 'strong-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO clockit_app;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
```

5. **Enable Database Encryption:**
```yaml
# In docker-compose.yml
services:
  clockit-db:
    image: postgres:15-alpine
    command: postgres -c ssl=on -c ssl_cert_file=/etc/ssl/certs/server.crt -c ssl_key_file=/etc/ssl/private/server.key
    volumes:
      - ./certs/server.crt:/etc/ssl/certs/server.crt:ro
      - ./certs/server.key:/etc/ssl/private/server.key:ro
```

6. **Setup Log Aggregation:**
```yaml
# Add logging service to docker-compose.yml
  logging:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
```

7. **Enable Security Scanning:**
```yaml
# Add to .github/workflows/ci.yml
- name: Run Trivy security scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'clockit:latest'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

---

## Testing Security Fixes

### Security Test Suite

**Create `tests/test_security.py`:**
```python
"""
Security-focused tests
"""
import pytest
from fastapi.testclient import TestClient

def test_password_strength_requirements(client: TestClient):
    """Test strong password requirements"""
    weak_passwords = [
        "123456",
        "password",
        "abc123",
        "Pass1",  # Too short
        "password123",  # No special char
        "PASSWORD123!",  # No lowercase
    ]
    
    for weak_pass in weak_passwords:
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": weak_pass
        })
        assert response.status_code == 400

def test_rate_limiting(client: TestClient):
    """Test rate limiting on login endpoint"""
    for i in range(10):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
    
    # Should be rate limited after too many attempts
    assert response.status_code == 429

def test_https_redirect(client: TestClient):
    """Test HTTPS redirect in production"""
    # Test with production environment
    response = client.get("/", headers={"X-Forwarded-Proto": "http"})
    assert response.status_code in [301, 307, 308]

def test_security_headers(client: TestClient):
    """Test security headers are present"""
    response = client.get("/")
    
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "Content-Security-Policy" in response.headers

def test_sql_injection_prevention(client: TestClient):
    """Test SQL injection attempts are handled"""
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
    ]
    
    for malicious in malicious_inputs:
        response = client.post("/auth/login", json={
            "email": malicious,
            "password": "password"
        })
        # Should not cause server error
        assert response.status_code in [400, 401]

def test_xss_prevention(client: TestClient):
    """Test XSS prevention in inputs"""
    xss_payload = "<script>alert('XSS')</script>"
    
    response = client.post("/tasks", json={
        "name": xss_payload,
        "description": "test",
        "category": "test"
    }, headers={"Authorization": "Bearer valid_token"})
    
    # Payload should be sanitized
    if response.status_code == 200:
        task_data = response.json()
        assert "<script>" not in task_data.get("task_name", "")
```

---

## Monitoring and Maintenance

### Regular Security Tasks:

1. **Weekly:**
   - Review failed login attempts
   - Check for unusual API access patterns
   - Review security logs

2. **Monthly:**
   - Update dependencies (npm audit, pip-audit)
   - Review and rotate credentials
   - Security scan with automated tools

3. **Quarterly:**
   - Full security audit
   - Penetration testing
   - Review and update security policies

4. **Annually:**
   - Third-party security assessment
   - Update security documentation
   - Security training for team

---

## Conclusion

Implementing these recommendations will significantly improve the security posture of the ClockIt platform. Priority should be given to:

1. **Critical fixes** (secret key, password policy) - Implement immediately
2. **High priority fixes** (HTTPS, CORS, credentials) - Implement before production
3. **Medium priority fixes** (rate limiting, monitoring) - Implement for production hardening
4. **Low priority fixes** (email verification, password reset) - Implement for feature completeness

Each fix has been designed to be backward compatible where possible and includes specific code examples for implementation.
