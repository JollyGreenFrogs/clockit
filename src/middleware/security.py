"""
Security middleware for HTTP security headers and HTTPS enforcement
"""
from fastapi import Request, Response
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from ..config import Config
except ImportError:
    from config import Config


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Strict-Transport-Security (HSTS) - only in production
        if Config.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
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
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        
        # Remove sensitive server headers
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response


def setup_security_middleware(app):
    """Configure security middleware for the application"""
    
    # HTTPS redirect in production only
    if Config.ENVIRONMENT == "production":
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Security headers for all environments
    app.add_middleware(SecurityHeadersMiddleware)
